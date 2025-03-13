# UMA Proposal Replayer UI

A web interface for exploring UMA proposal outputs and reruns.

## Features

- View both outputs and reruns in a tabular format
- Search functionality to filter results
- Detailed view showing all information in each JSON file
- Easy navigation with clickable rows

## Running the UI

### Option 1: Using the Python server (recommended)

1. Navigate to the UI directory:
   ```
   cd proposal_replayer/ui
   ```

2. Run the server:
   ```
   python server.py
   ```

3. This will automatically open your browser to http://localhost:8000/ui/

### Option 2: Using any HTTP server

You can serve the UI directory with any HTTP server. For example:

```
cd proposal_replayer
python -m http.server
```

Then open your browser to http://localhost:8000/ui/

## Usage

1. The UI displays two tabs: "Outputs" and "Reruns"
2. Each table shows the question ID, title, recommendation, and resolved price outcome
3. Click on any row or the "View" button to see detailed information
4. Use the search box to filter results

## Development

The UI is built with:
- HTML/CSS/JavaScript
- Bootstrap 5 for styling
- No build process required

Files:
- `index.html` - Main HTML structure
- `styles.css` - Custom CSS styles
- `app.js` - JavaScript for loading and displaying data
- `server.py` - Simple HTTP server for development 