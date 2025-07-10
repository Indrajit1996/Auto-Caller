from fastapi import APIRouter, Request
import boto3
import json
from datetime import datetime
import os

router = APIRouter()

# Use environment variables for region and Lambda ARN
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
LAMBDA_ARN = os.getenv('LAMBDA_ARN', 'arn:aws:lambda:us-west-2:123456789012:function:YOUR_LAMBDA_NAME')

eventbridge = boto3.client('events', region_name=AWS_REGION)

@router.post("/schedule-call")
async def schedule_call(request: Request):
    data = await request.json()
    to = data["to"]
    message = data["message"]
    scheduled_time = data["scheduled_time"]  # ISO8601 string

    dt = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
    cron_expr = f"cron({dt.minute} {dt.hour} {dt.day} {dt.month} ? {dt.year})"
    rule_name = f"call-{to.replace('+','')}-{dt.strftime('%Y%m%d%H%M%S')}"

    eventbridge.put_rule(
        Name=rule_name,
        ScheduleExpression=cron_expr,
        State='ENABLED'
    )

    eventbridge.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',
                'Arn': LAMBDA_ARN,
                'Input': json.dumps({
                    "to": to,
                    "message": message
                })
            }
        ]
    )
    return {"status": "scheduled", "rule_name": rule_name, "scheduled_time": scheduled_time} 