# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in MNN Pipeline, please report it by emailing the maintainers directly. **Do not open a public issue.**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

We will respond within 48 hours and work with you to understand and address the issue.

## Security Best Practices

### For Users

1. **Use Strong Passwords**: If configuring PostgreSQL, use strong, randomly generated passwords
2. **Limit Network Exposure**: Bind the API to `127.0.0.1` (localhost) unless external access is required
3. **Enable HTTPS**: Use a reverse proxy (nginx, traefik) with TLS certificates in production
4. **Environment Variables**: Never commit `.env` files with real credentials to version control
5. **Database Security**:
   - Enable SSL for database connections in production
   - Use restricted database users with minimal privileges
   - Regularly backup database data
6. **Rate Limiting**: Enable rate limiting to prevent abuse:
   ```bash
   export RATE_LIMIT_ENABLED=true
   export RATE_LIMIT_REQUESTS=100
   export RATE_LIMIT_WINDOW=60
   ```
7. **Logging**: Monitor logs for suspicious activity
8. **Updates**: Keep dependencies up to date to receive security patches

### For Developers

1. **Input Validation**: Always validate and sanitize user inputs
2. **SQL Injection**: Use parameterized queries (already implemented)
3. **Authentication**: Implement proper authentication before deploying to production
4. **Secrets Management**: Use environment variables, never hardcode secrets
5. **Security Headers**: Keep security headers middleware enabled
6. **Dependency Scanning**: Regularly scan dependencies for vulnerabilities:
   ```bash
   pip install safety
   safety check
   ```
7. **Code Review**: Review all code changes for security implications
8. **Testing**: Include security tests in the test suite

## Known Security Considerations

### Current Limitations

1. **No Authentication**: The API does not include authentication by default. This is suitable for:
   - Internal networks with trusted users
   - Development and testing
   - Deployment behind an authenticated proxy

   **For production internet-facing deployments**, implement authentication (JWT, OAuth2, or API keys).

2. **CORS**: CORS is configured to allow all origins by default. Update `api.py` to restrict origins:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specify actual origins
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **Rate Limiting**: Disabled by default. Enable for production:
   ```bash
   export RATE_LIMIT_ENABLED=true
   ```

## Security Features Implemented

- ✅ Parameterized SQL queries (SQL injection prevention)
- ✅ Input validation and length limits
- ✅ Security headers (HSTS, CSP, X-Frame-Options, X-XSS-Protection)
- ✅ Request ID tracking for audit trails
- ✅ Structured logging with client IP addresses
- ✅ Query sanitization (remove control characters, check for repetition)
- ✅ Configurable rate limiting
- ✅ CORS middleware (configurable)
- ✅ Connection timeout configuration
- ✅ Health check endpoint for monitoring

## Roadmap

Future security enhancements planned:
- JWT-based authentication
- API key management system
- Role-based access control (RBAC)
- Request signing for API clients
- Enhanced audit logging
- Integration with security scanning tools

## Disclosure Policy

We follow responsible disclosure:
1. Report received and acknowledged (48 hours)
2. Issue confirmed and assessed (1 week)
3. Fix developed and tested (2-4 weeks)
4. Security advisory published (after fix is released)
5. CVE assigned if applicable

Thank you for helping keep MNN Pipeline secure!
