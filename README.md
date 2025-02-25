# T4 GPU Development Environment for Unsloth Tasks

This repository contains code to set up a CloudFormation stack with a Tesla T4 GPU EC2 instance on AWS. It's designed to help you work on the Unsloth tasks that require a T4 GPU while saving you from Colab hell.

## Prerequisites

1. An AWS account with appropriate permissions
2. AWS CLI configured with your credentials
3. Python 3.9
4. An EC2 key pair for SSH access
5. Your public IP address (for secure SSH access)

## Setup

### 1. Install Dependencies

For setting up the infrastructure:
```bash
pip install ".[infra]"
```

### 2. Deploy the Stack

To create the CloudFormation stack:

```bash
python infrastructure/deploy.py --action create --my-ip YOUR_IP_ADDRESS --key-name YOUR_KEY_PAIR_NAME
```

Replace:
- `YOUR_IP_ADDRESS` with your public IP (e.g., `1.2.3.4` or `1.2.3.4/32`)
- `YOUR_KEY_PAIR_NAME` with the name of your EC2 key pair

### 3. Connect to the Instance

After the stack is created successfully, you'll see the SSH command:

```bash
ssh -i your-key.pem ec2-user@YOUR_INSTANCE_IP
```

### 4. Install Project Dependencies

Once connected to the instance, install your project dependencies:

```bash
cd ~/unsloth-tasks
pip install -e ".[core]"
pip install ".[core-depless]" --no-deps
```

### 5. Verify GPU Setup

Run the GPU verification script:

```bash
cd ~/unsloth-tasks
python scripts/gpu_check.py
```

## Managing the Stack

### Check Status

```bash
python infrastructure/deploy.py --action status
```

### Update Stack

```bash
python infrastructure/deploy.py --action update --my-ip NEW_IP_ADDRESS --key-name YOUR_KEY_PAIR_NAME
```

### Delete Stack

When you're done with the tasks and want to avoid further charges:

```bash
python infrastructure/deploy.py --action delete
```

## Cost Management

- The stack includes a CloudWatch alarm that automatically stops the instance after 2 hours of low CPU usage
- You can enable auto-shutdown by uncommenting the relevant line in the CloudFormation template
- Always delete the stack when you're done to avoid unexpected charges

## Important Notes

- The CloudFormation template uses a `g4dn.xlarge` instance by default, which includes 1 Tesla T4 GPU
- The AMI IDs in the template need to be updated with actual Deep Learning AMI IDs for each region
- Be careful with security - the template restricts SSH access to your IP address only
- Update the repository URL in the `UserData` section of the CloudFormation template
- Parameters like API keys should be stored in AWS Systems Manager Parameter Store

## Dependency Structure

The project uses optional dependency groups in `pyproject.toml`:

- `infra`: AWS infrastructure dependencies (boto3) for deployment
- `core`: Main ML dependencies needed for Unsloth tasks
- `core-depless`: Dependencies that need to be installed with `--no-deps` flag
- `dev`: Development tools like pytest, black, etc.

## Troubleshooting

### Common Issues

1. **GPU not detected**: Ensure the instance has started correctly and check the cloud-init logs:
   ```bash
   sudo cat /var/log/cloud-init-output.log
   ```

2. **SSH connection issues**: Verify your IP address hasn't changed and update if needed:
   ```bash
   python infrastructure/deploy.py --action update --my-ip NEW_IP_ADDRESS --key-name YOUR_KEY_PAIR_NAME
   ```

3. **CUDA errors**: Check driver compatibility:
   ```bash
   nvidia-smi
   ```

4. **Dependency issues with Unsloth packages**: Make sure you've installed them with the `--no-deps` flag:
   ```bash
   pip install ".[core-depless]" --no-deps
   ```

## Customizing

You can customize the CloudFormation template to:
- Use a different instance type (e.g., `g4dn.2xlarge` for more CPU/RAM)
- Change the volume size
- Add additional security groups or resources
- Modify the initialization script

## Development Workflow

1. **Infrastructure Setup**:
   ```bash
   # Install infrastructure dependencies
   pip install ".[infra]"
   
   # Deploy the stack
   python infrastructure/deploy.py --action create --my-ip YOUR_IP --key-name YOUR_KEY
   ```

2. **Development on EC2**:
   ```bash
   # SSH into the instance
   ssh -i your-key.pem ec2-user@YOUR_INSTANCE_IP
   
   # Install dependencies
   cd ~/unsloth-tasks
   pip install -e ".[core]"
   pip install ".[core-depless]" --no-deps
   
   # Run tasks
   python -m src.tasks.task1
   ```

3. **Cleanup**:
   ```bash
   python infrastructure/deploy.py --action delete
   ```

## License

[MIT License](LICENSE)
