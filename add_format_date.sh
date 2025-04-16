#!/bin/bash

# Create temporary files
head -n 4270 ui/app.js > ui/app.js.part1
tail -n +4270 ui/app.js > ui/app.js.part2

# Create the formatDate function content
cat << 'EOT' > ui/app.js.formatdate

// Helper function to format date in 24-hour format with seconds
function formatDate(timestamp) {
    // Only return N/A if timestamp is null or undefined, not if it's 0
    if (timestamp === null || timestamp === undefined) return 'N/A';
    
    try {
        // Handle string timestamps that are in ISO format
        if (typeof timestamp === 'string') {
            // Check for DD-MM-YYYY HH:MM format (e.g., "01-04-2025 21:15")
            if (timestamp.match(/^\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}$/)) {
                const [datePart, timePart] = timestamp.split(' ');
                const [day, month, year] = datePart.split('-');
                const [hours, minutes] = timePart.split(':');
                const date = new Date(year, month - 1, day, hours, minutes);
                if (!isNaN(date.getTime())) {
                    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
                }
            }
            
            // Try parsing as ISO format
            if (timestamp.includes('T') || timestamp.includes('-')) {
                const date = new Date(timestamp);
                if (!isNaN(date.getTime())) {
                    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
                }
            }
            
            // Try parsing as numeric string
            if (!isNaN(parseInt(timestamp, 10))) {
                timestamp = parseInt(timestamp, 10);
            } else {
                return timestamp; // Return the string as-is if we can't parse it
            }
        }
        
        // For numeric timestamps, assume Unix timestamp (seconds since epoch)
        if (typeof timestamp === 'number') {
            // If timestamp is in milliseconds (> year 2001), convert to seconds
            if (timestamp > 1000000000000) {
                timestamp = Math.floor(timestamp / 1000);
            }
            
            const date = new Date(timestamp * 1000);
            return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
        }
        
        // Fallback for unknown formats
        return String(timestamp);
    } catch (error) {
        console.warn('Error formatting date:', error, timestamp);
        return String(timestamp);
    }
}
EOT

# Combine the files
cat ui/app.js.part1 ui/app.js.formatdate ui/app.js.part2 > ui/app.js.new

# Replace the original file
mv ui/app.js.new ui/app.js

# Clean up temp files
rm ui/app.js.part1 ui/app.js.part2 ui/app.js.formatdate

echo "formatDate function has been added." 