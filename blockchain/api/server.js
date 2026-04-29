const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');
const crypto = require('crypto');
const fs = require('fs/promises');
const path = require('path');
const os = require('os');

const app = express();
app.use(cors());
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

// Configuration for Fabric test-network
const channelName = process.env.CHANNEL_NAME || 'mychannel';
const chaincodeName = process.env.CHAINCODE_NAME || 'zkp-ledger';
const mspId = process.env.MSP_ID || 'Org1MSP';

// Path to crypto materials (adjust if needed depending on fabric-samples location)
let cryptoPath = process.env.CRYPTO_PATH;
if (!cryptoPath) {
    if (os.platform() === 'win32') {
        // If you are running the Node API from Windows PowerShell/CMD, 
        // it needs to look into the WSL Ubuntu filesystem where Fabric is running.
        cryptoPath = '\\\\wsl$\\Ubuntu\\home\\anvit\\fabric-samples\\test-network\\organizations\\peerOrganizations\\org1.example.com';
    } else {
        // If running inside WSL
        cryptoPath = path.resolve(os.homedir(), 'fabric-samples', 'test-network', 'organizations', 'peerOrganizations', 'org1.example.com');
    }
}

const keyDirectoryPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'keystore');
const certPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'signcerts', 'User1@org1.example.com-cert.pem');
const tlsCertPath = path.resolve(cryptoPath, 'peers', 'peer0.org1.example.com', 'tls', 'ca.crt');
const peerEndpoint = process.env.PEER_ENDPOINT || 'localhost:7051';
const peerHostAlias = process.env.PEER_HOST_ALIAS || 'peer0.org1.example.com';

async function newGrpcConnection() {
    const tlsRootCert = await fs.readFile(tlsCertPath);
    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
    return new grpc.Client(peerEndpoint, tlsCredentials, {
        'grpc.ssl_target_name_override': peerHostAlias,
    });
}

async function newIdentity() {
    const credentials = await fs.readFile(certPath);
    return { mspId, credentials };
}

async function newSigner() {
    const files = await fs.readdir(keyDirectoryPath);
    const keyPath = path.resolve(keyDirectoryPath, files[0]);
    const privateKeyPem = await fs.readFile(keyPath);
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
}

// Global variables for Fabric connection
let gateway;
let contract;

async function initFabric() {
    console.log('Initializing Fabric connection...');
    const client = await newGrpcConnection();
    const gatewayInstance = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
        evaluateOptions: () => { return { deadline: Date.now() + 5000 }; },
        endorseOptions: () => { return { deadline: Date.now() + 15000 }; },
        submitOptions: () => { return { deadline: Date.now() + 5000 }; },
        commitStatusOptions: () => { return { deadline: Date.now() + 1 * 60000 }; },
    });
    gateway = gatewayInstance;
    const network = gateway.getNetwork(channelName);
    contract = network.getContract(chaincodeName);
    console.log('Fabric connection established successfully.');
}

// API Endpoints
app.post('/api/blocks', async (req, res) => {
    try {
        const { blockId, txCount, verificationTime, merkleRoot } = req.body;
        console.log(`Submitting CreateBlock transaction for ${blockId}`);
        
        await contract.submitTransaction(
            'CreateBlock',
            blockId,
            txCount.toString(),
            verificationTime.toString(),
            merkleRoot
        );
        
        res.status(200).json({ success: true, message: `Block ${blockId} recorded on ledger.` });
    } catch (error) {
        console.error('Error submitting transaction:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/blocks/:id', async (req, res) => {
    try {
        const blockId = req.params.id;
        const resultBytes = await contract.evaluateTransaction('ReadBlock', blockId);
        const resultJson = Buffer.from(resultBytes).toString('utf8');
        res.status(200).json(JSON.parse(resultJson));
    } catch (error) {
        console.error('Error evaluating transaction:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(PORT, async () => {
    console.log(`Server listening on port ${PORT}`);
    try {
        await initFabric();
    } catch (error) {
        console.error('Failed to connect to Fabric (Is the test-network running?):', error.message);
        // Do not exit, allow the user to start the network later and restart the app.
    }
});
