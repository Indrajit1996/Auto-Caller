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
    try:
        data = await request.json()
        print(f"Received data: {data}")
        to = data["to"]
        message = data["message"]
        call_type = data.get("call_type", "one-time")

        if call_type == "one-time":
            scheduled_time = data["scheduled_time"]  # ISO8601 string
            dt = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
            cron_expr = f"cron({dt.minute} {dt.hour} {dt.day} {dt.month} ? {dt.year})"
            rule_name = f"call-{to.replace('+','')}-{dt.strftime('%Y%m%d%H%M%S')}"
        else:
            # Recurring call
            recurring_time = data.get("recurring_time") or data.get("recurrence_time")  # ISO8601 string
            recurring_days = data.get("recurring_days") or data.get("recurrence_day", [])  # List of day indices (0=Sun, 1=Mon, etc.)
            recurrence_pattern = data.get("recurrence_pattern", "weekly")
            
            if not recurring_time:
                return {"status": "error", "detail": "recurrence_time is required for recurring calls"}
            if not recurring_days:
                return {"status": "error", "detail": "recurrence_day is required for recurring calls"}
            if not recurrence_pattern:
                return {"status": "error", "detail": "recurrence_pattern is required for recurring calls"}
            
            dt = datetime.fromisoformat(recurring_time.replace("Z", "+00:00"))
            
            # Convert day indices to AWS cron format (1=Sun, 2=Mon, etc.)
            day_list = ",".join([str(d + 1) for d in recurring_days])
            
            cron_expr = f"cron({dt.minute} {dt.hour} ? * {day_list} *)"
            rule_name = f"recurring-call-{to.replace('+','')}-{dt.strftime('%H%M')}"

        print(f"Creating EventBridge rule: {rule_name}")
        print(f"Cron expression: {cron_expr}")

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
        
        if call_type == "one-time":
            return {"status": "scheduled", "rule_name": rule_name, "scheduled_time": scheduled_time}
        else:
            return {"status": "scheduled", "rule_name": rule_name, "recurring_time": recurring_time, "recurring_days": recurring_days}
    except Exception as e:
        print(f"Error scheduling call: {str(e)}")
        return {"status": "error", "detail": str(e)}