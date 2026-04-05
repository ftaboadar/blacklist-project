"""
Entry point - AWS Elastic Beanstalk requires this file named 'application.py'
and the Flask app object named 'application'.
"""
from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=False)
