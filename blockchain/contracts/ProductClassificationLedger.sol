// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProductClassificationLedger {
    struct ClassificationRecord {
        uint256 id;
        string productId;
        string objectName;
        string color;
        string result;
        string rgbValue;
        string hsvValue;
        uint256 confidence;
        string resultHash;
        uint256 timestamp;
        address operator;
    }

    uint256 public totalRecords;
    address public owner;

    mapping(uint256 => ClassificationRecord) private records;
    mapping(string => uint256[]) private productIndex;

    event ClassificationLogged(
        uint256 indexed id,
        string indexed productId,
        string color,
        string result,
        uint256 confidence,
        string resultHash,
        uint256 timestamp,
        address indexed operator
    );

    constructor() {
        owner = msg.sender;
    }

    function addRecord(
        string memory productId,
        string memory objectName,
        string memory color,
        string memory result,
        string memory rgbValue,
        string memory hsvValue,
        uint256 confidence,
        string memory resultHash,
        uint256 timestamp
    ) public returns (uint256) {
        totalRecords += 1;
        records[totalRecords] = ClassificationRecord({
            id: totalRecords,
            productId: productId,
            objectName: objectName,
            color: color,
            result: result,
            rgbValue: rgbValue,
            hsvValue: hsvValue,
            confidence: confidence,
            resultHash: resultHash,
            timestamp: timestamp,
            operator: msg.sender
        });
        productIndex[productId].push(totalRecords);
        emit ClassificationLogged(totalRecords, productId, color, result, confidence, resultHash, timestamp, msg.sender);
        return totalRecords;
    }

    function addClassification(
        string memory productId,
        string memory objectName,
        string memory color,
        string memory result,
        string memory rgbValue,
        string memory hsvValue,
        uint256 timestamp
    ) public returns (uint256) {
        return addRecord(productId, objectName, color, result, rgbValue, hsvValue, 0, "", timestamp);
    }

    function getRecord(uint256 id) public view returns (ClassificationRecord memory) {
        require(id > 0 && id <= totalRecords, "Record does not exist");
        return records[id];
    }

    function getProductRecordIds(string memory productId) public view returns (uint256[] memory) {
        return productIndex[productId];
    }
}
