resource "aws_dynamodb_table" "transactions_table" {
  name           = "Transactions"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "userId"
  range_key      = "transactionId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "transactionId"
    type = "S"
  }

  attribute {
    name = "location"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name               = "LocationTimestampIndex"
    key_schema {
        attribute_name = "location"
        key_type       = "HASH"
    }
    key_schema {
        attribute_name = "timestamp"
        key_type       = "RANGE"
    }
    write_capacity     = 5
    read_capacity      = 5
    projection_type    = "ALL" 
  }
}