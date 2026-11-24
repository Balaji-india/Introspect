"""Scheduled job (EventBridge Scheduler -> Lambda): builds each consenting user's morning brief.

Prototype: runs the pipeline on the configured data folder. Hack-day plan: iterate over users
in the DynamoDB consent ledger who granted 'cloud_narration' and push the brief to their app.
"""
from introspect import config, pipeline


def handler(event=None, context=None):
    res = pipeline.run(config.DATA_DIR)
    return {"brief": res["brief"], "readiness_today": res["facts"]["readiness_today"]}


if __name__ == "__main__":
    print(handler())
