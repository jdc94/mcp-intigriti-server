# MCP Intigriti Server

A Model Context Protocol (MCP) server for the Intigriti Researcher API, enabling security researchers to interact with Intigriti's bug bounty platform through Claude Desktop.

## Features

- **Complete API Coverage**: All 5 endpoints from Intigriti's Researcher API v1.0
- **Real-time Program Data**: Access live bug bounty programs, scope, and activities
- **Claude Desktop Integration**: Seamless integration with Claude Desktop
- **Researcher Focused**: Built by bug bounty hunters, for bug bounty hunters

## Prerequisites

- **Python 3.10 or higher** (required for MCP)
- **Intigriti researcher account** with API access
- **Claude Desktop** application

## Quick Setup

### 1. Install Python Dependencies

```bash
pip install mcp httpx pydantic
```

### 2. Get Your Intigriti API Token

1. Log into your [Intigriti researcher account](https://app.intigriti.com/)
2. Navigate to your profile settings
3. Generate a new **Researcher API** token
4. Copy the token for configuration

### 3. Download the Server

```bash
# Clone this repository
git clone https://github.com/yourusername/mcp-intigriti-server.git
cd mcp-intigriti-server

# Note the full path to server.py
pwd
# Copy this path - you'll need it for Claude configuration
```

### 4. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**Config File Location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "intigriti": {
      "command": "python3",
      "args": ["/full/path/to/server.py"],
      "env": {
        "INTIGRITI_API_TOKEN": "your_intigriti_api_token_here"
      }
    }
  }
}
```

**Important Notes:**
- Replace `/full/path/to/server.py` with the actual path to your downloaded server.py file
- Replace `your_intigriti_api_token_here` with your actual Intigriti API token
- Ensure you have Python 3.10+ with MCP dependencies installed

### 5. Restart Claude Desktop

1. Quit Claude Desktop completely
2. Wait a few seconds
3. Open Claude Desktop again

### 6. Test the Integration

In Claude Desktop, try asking:

```
"What MCP tools do you have available?"
```

You should see Intigriti tools listed in the response.

**Alternative: Test in Developer Tools**

You can also verify the connection in Claude Desktop's developer tools:
1. Open Claude Desktop
2. Go to **Settings** > **Developer**
3. Check the **MCP** section to see if your Intigriti server is connected
4. View any connection logs or errors

## Available Tools

| Tool | Description |
|------|-------------|
| `get_programs` | List all accessible programs with filtering options |
| `get_program_details` | Get detailed information about a specific program |
| `get_program_activities` | View recent program activities and updates |
| `get_program_domains` | Get program scope and testing domains |
| `get_program_rules_of_engagement` | Get program rules and testing requirements |

## Usage Examples

### Finding Programs
```
"Show me all active bug bounty programs with high rewards"
"Find mobile application testing programs"
"What are the newest programs added this week?"
```

### Program Research
```
"Get complete details for program ID 'abc-123-def' including scope"
"Show me the testing domains for Program1's bug bounty program"
"What are the rules of engagement for this e-commerce platform?"
```

### Activity Monitoring
```
"What activities have happened in programs I'm following?"
"Show me recent updates from all bug bounty programs"
"Has there been any activity since yesterday?"
```

## API Endpoints

Based on [Intigriti's OpenAPI specification](https://api.intigriti.com/external/researcher/swagger/index.html):

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/v1/programs` | GET | List all accessible programs |
| `/v1/programs/{id}` | GET | Get program details |
| `/v1/programs/activities` | GET | Get program activities |
| `/v1/programs/{id}/domains/{versionId}` | GET | Get program domains |
| `/v1/programs/{id}/rules-of-engagements/{versionId}` | GET | Get rules of engagement |

## Troubleshooting

### "No module named 'mcp'" Error

This means your Python environment doesn't have the MCP dependencies installed:

```bash
# Install the required dependencies
pip install mcp httpx pydantic

# Or if you have multiple Python versions, be specific
python3 -m pip install mcp httpx pydantic

# Otherwise

pip install "mcp[cli]"
```

### "Authentication failed" Error

- Verify your API token is correct and hasn't expired
- Ensure you have researcher API access enabled in Intigriti
- Check that the token is properly set in the Claude config

### Connection Timeout

- Verify the server.py file path is correct in your Claude config
- Ensure Python dependencies are installed: `pip install mcp httpx pydantic`
- Check that Python 3.10+ is being used

### Server Not Showing in Claude

- Restart Claude Desktop completely after configuration changes
- Verify the configuration file syntax is valid JSON
- Check the Claude Desktop logs for error messages

## Compatibility

This server is designed for **Claude Desktop** but the MCP protocol is universal. It can work with other MCP-compatible clients including:

- Cursor IDE
- Other MCP-enabled development tools
- Custom MCP client implementations

For other clients, use the same server.py file with your client's MCP configuration format.