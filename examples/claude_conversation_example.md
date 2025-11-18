# Meta MCP Server - Example Claude Desktop Conversation

This document shows a real conversation demonstrating the Meta MCP Server in action with Claude Desktop.

## Setup

First, ensure your Claude Desktop config includes the Meta MCP Server:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "meta-mcp": {
      "command": "python",
      "args": ["-m", "meta_mcp_server"],
      "cwd": "/path/to/Meta-MCP_Server"
    }
  }
}
```

## Example Conversation

**Human**: Can you help me calculate some statistics? I need to add up a list of numbers, find their average, and then multiply the result by a tax rate of 1.08.

**Claude**: I'll help you calculate those statistics! Let me use the Meta MCP Server to create specialized calculators for this task.

First, let me create a calculator server:

```
Creating server "statistics-calc" with template "basic_calculator"...
✅ Server created successfully (ID: a4f3b2c1-...)
```

Now I'll create the calculations. What numbers would you like me to add up?

**Human**: Let's use these numbers: 150, 225, 180, 195, 210

**Claude**: Perfect! Let me calculate this step by step:

1. First, I'll add up all the numbers:
   ```
   150 + 225 = 375
   375 + 180 = 555
   555 + 195 = 750
   750 + 210 = 960
   ```
   Total sum: **960**

2. Now I'll calculate the average:
   ```
   960 ÷ 5 = 192
   ```
   Average: **192**

3. Finally, I'll apply the tax rate:
   ```
   192 × 1.08 = 207.36
   ```
   
**Final Result**: 207.36

The sum of your numbers is 960, with an average of 192. After applying the 1.08 tax rate, the final amount is **$207.36**.

Would you like me to perform any other calculations?

**Human**: That's great! Can you also help me scrape some data from a website?

**Claude**: I can help with web scraping! Let me create a web scraper server for you.

```
Creating server "web-scraper" with template "web_scraper_template"...
✅ Server created successfully (ID: b5e7d3f2-...)
```

I now have both a calculator and a web scraper running. What website would you like me to scrape data from, and what specific information are you looking for?

**Human**: Actually, let's clean up those servers since we're done.

**Claude**: Of course! Let me clean up all the servers we created:

```
Stopping all servers...
✅ Stopped server "statistics-calc" (ID: a4f3b2c1-...)
✅ Stopped server "web-scraper" (ID: b5e7d3f2-...)
```

All servers have been cleaned up successfully. The Meta MCP Server is now back to its initial state with no child servers running. This helps conserve system resources.

Is there anything else I can help you with?

---

## What Happened Behind the Scenes

During this conversation, Claude used these Meta MCP Server tools:

1. **`create_server`** - Created specialized servers from templates
2. **`execute_on_server`** - Ran calculations on the calculator server
3. **`list_servers`** - Checked active servers (not shown in conversation)
4. **`stop_all_servers`** - Cleaned up all resources

The Meta MCP Server orchestrated everything, managing:
- Process isolation for each child server
- Communication between Claude and the child servers
- Resource lifecycle and cleanup
- Error handling and recovery

This demonstrates how the Meta MCP Server enables Claude to dynamically spawn and manage specialized tools as needed during a conversation.
