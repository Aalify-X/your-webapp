from app import app as application

def handler(event=None, context=None):
    try:
        return app(event, context)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }

__handler__ = handler
