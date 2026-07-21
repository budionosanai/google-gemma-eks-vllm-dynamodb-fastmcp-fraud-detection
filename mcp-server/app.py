import boto3
import httpx
from boto3.dynamodb.conditions import Key
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


class FraudAnalysisResponse(BaseModel):
    status: str = Field(description="Transaction status, must be either 'FRAUD' or 'NOT FRAUD'")
    risk_score: int = Field(description="Risk score ranging from 0 to 100")
    reasons: str = Field(description="Reasons for the fraud analysis in English")


# JSON Schema
json_schema = FraudAnalysisResponse.model_json_schema()

# FastMCP Server
mcp = FastMCP("Simple Fraud Detection MCP Server")

# DynamoDB Table
dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
table = dynamodb.Table("Transactions")

# From Kubernetes gemma-4-vllm service
VLLM_URL = "http://gemma-4-vllm:8000/v1/chat/completions"


async def analyze_fraud_with_llm(transactions: list, current_amount: float, user_id: str) -> FraudAnalysisResponse:
    """
    Extracts history from DynamoDB and requests structured JSON from vLLM.
    """
    history_context = ""
    for tx in transactions[:5]:
        history_context += f"- TxID: {tx.get('transactionId')}, Amount: {tx.get('amount')}, Location: {tx.get('location')}, Timestamp: {tx.get('timestamp')}\n"

    if not history_context:
        history_context = "No previous transaction history found (New User)\n"

    system_prompt = """
    You are an expert AI Fraud Detection Specialist for a financial service platform.
    Analyze the user transaction history and determine whether the incoming transaction is suspicious (FRAUD) or safe (NOT FRAUD).
    You must respond using a strict JSON format matching the provided schema containing 'status', 'risk_score', and 'reasons'.
    Rules is status must be either "FRAUD" or "NOT FRAUD", risk_score must be an INTEGER from 0 to 100, do not return markdown, 
    do not explain anything and return JSON only.

    Example
    {
          "status": "FRAUD",
          "risk_score": 95,
          "reasons": ...
    }
    """

    user_prompt = f"""
    [DYNAMODB TRANSACTION HISTORY]
    {history_context}

    [NEW INCOMING TRANSACTION]
    User ID: {user_id}
    Amount: {current_amount}

    Analyze the pattern and determine the risk. Provide your response strictly inside the requested JSON schema.
    """

    payload = {
        "model": "google/gemma-4-E4B-it",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "fraud-analysis",
                "schema": FraudAnalysisResponse.model_json_schema()
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(VLLM_URL, json=payload, timeout=15.0)
        response.raise_for_status()
        raw = response.json()['choices'][0]['message']['content']
        return FraudAnalysisResponse.model_validate_json(raw)


@mcp.tool()
async def check_transaction_fraud(user_id: str, amount: float) -> str:
    """
    Evaluates potential fraud risks on a new transaction using historical 
    DynamoDB data and AI reasoning via vLLM with Structured Output.
    """
    try:
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id),
            Limit=10,
            ScanIndexForward=False
        )
        recent_transactions = response.get('Items', [])

        ai_result = await analyze_fraud_with_llm(recent_transactions, amount, user_id)
        status_icon = "⚠️ FRAUD DETECTED" if ai_result.status == "FRAUD" else "✅ NOT FRAUD"

        return (
            f"=== Fraud Analysis Report ===\n"
            f"Decision Status  : {status_icon}\n"
            f"User ID          : {user_id}\n"
            f"Evaluated Amount : {amount}\n"
            f"AI Risk Score    : {ai_result.risk_score}/100 \n"
            f"Analysis Reasons : {ai_result.reasons}"
        )
    except Exception as e:
        return f"Failed to analyze transaction via MCP server.\n{str(e)}"


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})


app = mcp.http_app()