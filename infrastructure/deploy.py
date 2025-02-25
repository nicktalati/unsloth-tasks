#!/usr/bin/env python3
"""
deploy.py - Deploy/update CloudFormation stack for T4 GPU development environment
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Constants
STACK_NAME = "t4-dev-environment"
TEMPLATE_FILE = "cloudformation.yaml"
REGION = "us-east-1"  # Change to your preferred region


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Deploy T4 GPU development environment")
    parser.add_argument("--action", choices=["create", "update", "delete", "status"],
                        required=True, help="Action to perform on the CloudFormation stack")
    parser.add_argument("--my-ip", help="Your IP address for SSH access (format: x.x.x.x/32)")
    parser.add_argument("--key-name", help="EC2 Key Pair name for SSH access")
    return parser.parse_args()


def read_template():
    """Read CloudFormation template file."""
    template_path = Path(__file__).parent / TEMPLATE_FILE
    if not template_path.exists():
        print(f"Error: Template file {TEMPLATE_FILE} not found")
        sys.exit(1)
    return template_path.read_text()


def get_stack_status(cf_client):
    """Get the current status of the stack."""
    try:
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        return response["Stacks"][0]["StackStatus"]
    except ClientError as e:
        if "does not exist" in str(e):
            return "DOES_NOT_EXIST"
        raise


def wait_for_stack_completion(cf_client, action):
    """Wait for the stack operation to complete."""
    print(f"Waiting for stack {action} to complete...", end="", flush=True)
    
    waiter_map = {
        "create": "stack_create_complete",
        "update": "stack_update_complete",
        "delete": "stack_delete_complete"
    }
    
    waiter = cf_client.get_waiter(waiter_map[action])
    
    try:
        while True:
            try:
                waiter.wait(StackName=STACK_NAME, WaiterConfig={"Delay": 5, "MaxAttempts": 1})
                break
            except ClientError as e:
                if "does not exist" in str(e) and action == "delete":
                    # Stack has been deleted
                    break
                # If we're waiting for a delete and the stack was deleted, we're done
                raise
            except:
                print(".", end="", flush=True)
                time.sleep(5)
        print(" Done!")
        return True
    except Exception as e:
        print(f"\nError waiting for stack: {e}")
        return False


def get_stack_outputs(cf_client):
    """Get the outputs from the CloudFormation stack."""
    try:
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response["Stacks"][0].get("Outputs", [])
        
        if not outputs:
            return {}
        
        return {output["OutputKey"]: output["OutputValue"] for output in outputs}
    except ClientError:
        return {}


def create_or_update_stack(cf_client, template, parameters, action):
    """Create or update the CloudFormation stack."""
    kwargs = {
        "StackName": STACK_NAME,
        "TemplateBody": template,
        "Parameters": parameters,
        "Capabilities": ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
    }
    
    try:
        if action == "create":
            cf_client.create_stack(**kwargs)
        else:  # update
            cf_client.update_stack(**kwargs)
        return wait_for_stack_completion(cf_client, action)
    except ClientError as e:
        if "No updates are to be performed" in str(e):
            print("No updates required for the stack.")
            return True
        print(f"Error {action} stack: {e}")
        return False


def delete_stack(cf_client):
    """Delete the CloudFormation stack."""
    try:
        cf_client.delete_stack(StackName=STACK_NAME)
        return wait_for_stack_completion(cf_client, "delete")
    except ClientError as e:
        print(f"Error deleting stack: {e}")
        return False


def print_stack_info(cf_client):
    """Print information about the stack."""
    status = get_stack_status(cf_client)
    
    if status == "DOES_NOT_EXIST":
        print(f"Stack {STACK_NAME} does not exist.")
        return
    
    print(f"Stack {STACK_NAME} status: {status}")
    
    if status.endswith("_COMPLETE") and not status.startswith("DELETE"):
        outputs = get_stack_outputs(cf_client)
        if outputs:
            print("\nStack Outputs:")
            for key, value in outputs.items():
                print(f"  {key}: {value}")
        
        # Get instance information
        ec2 = boto3.client('ec2', region_name=REGION)
        response = cf_client.describe_stack_resources(StackName=STACK_NAME)
        
        instance_ids = []
        for resource in response["StackResources"]:
            if resource["ResourceType"] == "AWS::EC2::Instance":
                instance_ids.append(resource["PhysicalResourceId"])
        
        if instance_ids:
            print("\nInstance Info:")
            instances = ec2.describe_instances(InstanceIds=instance_ids)
            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    print(f"  Instance ID: {instance['InstanceId']}")
                    print(f"  State: {instance['State']['Name']}")
                    print(f"  Instance Type: {instance['InstanceType']}")
                    if 'PublicIpAddress' in instance:
                        print(f"  Public IP: {instance['PublicIpAddress']}")
                    print(f"  SSH Command: ssh -i your-key.pem ec2-user@{instance.get('PublicIpAddress', 'N/A')}")


def main():
    """Main function."""
    args = parse_args()
    
    # Initialize AWS clients
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    # Check current stack status
    current_status = get_stack_status(cf_client)
    
    # Handle action
    if args.action == "status":
        print_stack_info(cf_client)
        return
    
    if args.action == "delete":
        if current_status == "DOES_NOT_EXIST":
            print(f"Stack {STACK_NAME} does not exist.")
            return
        print(f"Deleting stack {STACK_NAME}...")
        success = delete_stack(cf_client)
        if success:
            print(f"Stack {STACK_NAME} deleted successfully.")
        return
    
    # For create/update actions
    if args.action in ["create", "update"]:
        if args.action == "create" and current_status != "DOES_NOT_EXIST":
            print(f"Stack {STACK_NAME} already exists. Use --action update to update it.")
            return
        if args.action == "update" and current_status == "DOES_NOT_EXIST":
            print(f"Stack {STACK_NAME} does not exist. Use --action create to create it.")
            return
            
        # Validate required parameters
        if not args.my_ip or not args.key_name:
            print("Error: --my-ip and --key-name are required for create/update actions.")
            return
            
        # Make sure IP is in CIDR format
        if not args.my_ip.endswith("/32"):
            args.my_ip = f"{args.my_ip}/32"
        
        # Read CloudFormation template
        template = read_template()
        
        # Prepare parameters
        parameters = [
            {"ParameterKey": "MyIpAddress", "ParameterValue": args.my_ip},
            {"ParameterKey": "KeyName", "ParameterValue": args.key_name}
        ]
        
        print(f"{args.action.capitalize()}ing stack {STACK_NAME}...")
        success = create_or_update_stack(cf_client, template, parameters, args.action)
        
        if success:
            print(f"Stack {STACK_NAME} {args.action}d successfully.")
            print_stack_info(cf_client)
        

if __name__ == "__main__":
    main()
