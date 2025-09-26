# GitHub Actions Configuration (немного почистил)

## Required Secrets

Set these secrets in your GitHub repository settings:
`Settings > Secrets and variables > Actions > Repository secrets`

### Bot Configuration
- `BOT_TOKEN` - Your Telegram bot token
- `ADMIN_IDS` - Comma-separated list of admin user IDs

### Database Configuration
- `DATABASE_URL` - PostgreSQL connection string for production
- `REDIS_URL` - Redis connection string (optional)

### Server Configuration
- `SSH_PRIVATE_KEY` - Private SSH key for server access
- `SERVER_USER` - Username for server access
- `SERVER_HOST` - Server hostname or IP address

### Notification Configuration
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

### Package Publishing
- `PYPI_API_TOKEN` - PyPI API token for package publishing

### Code Quality
- `SONAR_TOKEN` - SonarCloud token for code analysis

## Environment Variables

These can be set in workflow files or as repository variables:

### Python Configuration
- `PYTHON_VERSION` - Python version (default: 3.11)
- `PIP_CACHE_DIR` - Pip cache directory

### Docker Configuration
- `DOCKER_REGISTRY` - Docker registry URL
- `DOCKER_IMAGE` - Docker image name

### Database Configuration
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user

### Redis Configuration
- `REDIS_HOST` - Redis host
- `REDIS_PORT` - Redis port
- `REDIS_DB` - Redis database number

## Workflow Files

### CI/CD Workflows
- `ci.yml` - Main CI pipeline (tests, linting, security)
- `deploy.yml` - Production deployment
- `release.yml` - Package release to PyPI

### Quality Workflows
- `quality.yml` - Code quality analysis
- `security.yml` - Security scanning
- `lint.yml` - Code linting

### Monitoring Workflows
- `monitor.yml` - Health checks and monitoring
- `notify.yml` - Notifications for issues and PRs

### Utility Workflows
- `backup.yml` - Database backups
- `cleanup.yml` - Cleanup old artifacts
- `update.yml` - Dependency updates

## Usage Examples

### Using Secrets in Workflows
```yaml
env:
  BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
  ADMIN_IDS: ${{ secrets.ADMIN_IDS }}
```

### Using Environment Variables
```yaml
env:
  PYTHON_VERSION: '3.11'
  LOG_LEVEL: 'INFO'
```

### Using in Scripts
```bash
export BOT_TOKEN="${{ secrets.BOT_TOKEN }}"
export ADMIN_IDS="${{ secrets.ADMIN_IDS }}"
```

## Troubleshooting

### Common Issues
1. **Invalid context access** - Make sure secrets are set in repository settings
2. **Action input errors** - Update to latest action versions
3. **Permission denied** - Check repository permissions and token scopes

### Debugging
- Check workflow logs in GitHub Actions tab
- Verify secrets are set correctly
- Test workflows with `workflow_dispatch` trigger
