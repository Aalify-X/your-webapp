from app import app as application

def handler(event=None, context=None):
    return {
        'statusCode': 200,
        'body': 'Application is running'
    }

__handler__ = handler
