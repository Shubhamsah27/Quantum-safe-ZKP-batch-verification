package main

import (
	"encoding/json"
	"fmt"
	"log"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing a ZKP Block
type SmartContract struct {
	contractapi.Contract
}

// ZKPBlock describes basic details of what makes up a verified block.
type ZKPBlock struct {
	BlockID          string  `json:"blockId"`
	TxCount          int     `json:"txCount"`
	VerificationTime float64 `json:"verificationTime"`
	MerkleRoot       string  `json:"merkleRoot"`
}

// InitLedger adds a base block to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	genesisBlock := ZKPBlock{
		BlockID:          "block-0",
		TxCount:          0,
		VerificationTime: 0.0,
		MerkleRoot:       "00000000000000000000000000000000",
	}
	genesisBlockJSON, err := json.Marshal(genesisBlock)
	if err != nil {
		return err
	}
	err = ctx.GetStub().PutState(genesisBlock.BlockID, genesisBlockJSON)
	if err != nil {
		return fmt.Errorf("failed to put to world state. %v", err)
	}
	return nil
}

// CreateBlock issues a new ZKP block to the world state
func (s *SmartContract) CreateBlock(ctx contractapi.TransactionContextInterface, blockID string, txCount int, verificationTime float64, merkleRoot string) error {
	exists, err := s.BlockExists(ctx, blockID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the block %s already exists", blockID)
	}

	block := ZKPBlock{
		BlockID:          blockID,
		TxCount:          txCount,
		VerificationTime: verificationTime,
		MerkleRoot:       merkleRoot,
	}
	blockJSON, err := json.Marshal(block)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(blockID, blockJSON)
}

// ReadBlock returns the block stored in the world state with given id.
func (s *SmartContract) ReadBlock(ctx contractapi.TransactionContextInterface, blockID string) (*ZKPBlock, error) {
	blockJSON, err := ctx.GetStub().GetState(blockID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if blockJSON == nil {
		return nil, fmt.Errorf("the block %s does not exist", blockID)
	}

	var block ZKPBlock
	err = json.Unmarshal(blockJSON, &block)
	if err != nil {
		return nil, err
	}

	return &block, nil
}

// BlockExists returns true when block with given ID exists in world state
func (s *SmartContract) BlockExists(ctx contractapi.TransactionContextInterface, blockID string) (bool, error) {
	blockJSON, err := ctx.GetStub().GetState(blockID)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}
	return blockJSON != nil, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating zkp-ledger chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting zkp-ledger chaincode: %v", err)
	}
}
