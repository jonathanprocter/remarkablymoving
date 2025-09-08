#!/bin/bash

# Backup the original file
echo "Creating backup of index.html..."
cp index.html index.html.backup.$(date +%Y%m%d_%H%M%S)

# Create a temporary file for modifications
TMP_FILE="index.html.tmp"
cp index.html "$TMP_FILE"

echo "Applying fixes to index.html..."

# Fix 1: Replace Deploy to Replit with Share Project button
echo "1. Replacing Deploy button with Share button..."
sed -i 's/<i class="fas fa-rocket mr-2"><\/i>Deploy to Replit/<i class="fas fa-share-alt mr-2"><\/i>Share Project/g' "$TMP_FILE"
sed -i 's/id="deployToReplit"/id="shareProject"/g' "$TMP_FILE"

# Fix 2: Update button styles to rounded pills with emojis
echo "2. Updating button styles..."
sed -i 's/rounded-lg hover:bg-green-700 transition-colors">/rounded-full hover:bg-green-700 transition-all hover:scale-105 shadow-md">/g' "$TMP_FILE"
sed -i 's/rounded-lg hover:bg-purple-700 transition-colors">/rounded-full hover:bg-purple-700 transition-all hover:scale-105 shadow-md">/g' "$TMP_FILE"
sed -i 's/rounded-lg hover:bg-blue-700 transition-colors/rounded-full hover:bg-blue-700 transition-all hover:scale-105 shadow-md/g' "$TMP_FILE"
sed -i 's/<i class="fas fa-download mr-2"><\/i>Generate PDF/📊 Generate PDF/g' "$TMP_FILE"
sed -i 's/<i class="fas fa-share-alt mr-2"><\/i>Share Project/📤 Share Project/g' "$TMP_FILE"
sed -i 's/<i class="fas fa-sync-alt mr-2"><\/i>Sync Events/🔄 Sync Events/g' "$TMP_FILE"

# Fix 3: Update page navigation buttons
echo "3. Updating page navigation buttons..."
sed -i 's/rounded text-sm hover:bg-purple-700 transition-colors" data-page="0">Week/rounded-full text-sm hover:bg-purple-700 transition-all hover:scale-105 shadow-md" data-page="0">📅 Week/g' "$TMP_FILE"
sed -i 's/rounded text-sm hover:bg-gray-400 transition-colors"/rounded-full text-sm hover:bg-gray-400 transition-all hover:scale-105"/g' "$TMP_FILE"

# Fix 4: Replace deployToReplit function with shareProject function
echo "4. Replacing deployToReplit function with shareProject..."
cat > replace_function.tmp << 'EOF'
        // Share Project
        function shareProject() {
            // Get the current Replit URL
            const projectUrl = window.location.href;
            
            // Try to copy to clipboard
            navigator.clipboard.writeText(projectUrl).then(() => {
                // Show success notification
                const notification = document.createElement('div');
                notification.className = 'fixed top-4 right-4 bg-purple-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
                notification.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Project URL copied to clipboard!';
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 3000);
            }).catch(() => {
                // Fallback for browsers that don't support clipboard API
                prompt('Copy this URL to share your calendar generator:', projectUrl);
            });
        }
EOF

# Use perl for multi-line replacement
perl -i -0pe 's/\/\/ Deploy to Replit\s+function deployToReplit\(\) \{[^}]+\}[^}]+\}/'"$(cat replace_function.tmp | sed 's/[[\.*^$()+?{|]/\\&/g' | sed ':a;N;$!ba;s/\n/\\n/g')"'/g' "$TMP_FILE"

# Fix 5: Fix event spanning in weekly view (ensure proper height calculation)
echo "5. Fixing event spanning in weekly view..."
perl -i -pe 's/eventEl\.style\.height = `\$\{numSlots \* 16\}px`;/eventEl.style.height = `\$\{(numSlots * 16) - 1\}px`;/g' "$TMP_FILE"

# Fix 6: Fix event spanning in daily view (remove 2-slot limitation)
echo "6. Fixing event spanning in daily view..."
perl -i -pe 's/const slotsToSpan = Math\.min\(numSlots, 2\);/const actualSlots = numSlots;/g' "$TMP_FILE"
perl -i -pe 's/const totalHeight = \(slotsToSpan \* 30\) - 2;/const totalHeight = (actualSlots * 24) - 2;/g' "$TMP_FILE"

# Fix 7: Add null checks for addEventListener
echo "7. Adding null checks for event listeners..."
perl -i -pe 's/document\.getElementById\('"'"'authButton'"'"'\)\.addEventListener/const authButton = document.getElementById('"'"'authButton'"'"'); if (authButton) authButton.addEventListener/g' "$TMP_FILE"
perl -i -pe 's/document\.getElementById\('"'"'syncNow'"'"'\)\.addEventListener/const syncButton = document.getElementById('"'"'syncNow'"'"'); if (syncButton) syncButton.addEventListener/g' "$TMP_FILE"
perl -i -pe 's/document\.getElementById\('"'"'generatePDF'"'"'\)\.addEventListener/const pdfButton = document.getElementById('"'"'generatePDF'"'"'); if (pdfButton) pdfButton.addEventListener/g' "$TMP_FILE"
perl -i -pe 's/document\.getElementById\('"'"'shareProject'"'"'\)\.addEventListener/const shareButton = document.getElementById('"'"'shareProject'"'"'); if (shareButton) shareButton.addEventListener/g' "$TMP_FILE"

# Fix 8: Add weeklyEvents global variable
echo "8. Adding weeklyEvents global variable..."
sed -i '/let calendarEvents = \[\];/a\        let weeklyEvents = {}; \/\/ Add this to fix PDF generation errors' "$TMP_FILE"

# Fix 9: Fix duration calculation for exact 60-minute events
echo "9. Fixing duration calculation..."
perl -i -pe 's/const numSlots = Math\.ceil\(durationMinutes \/ 30\);/const numSlots = durationMinutes === 60 ? 2 : Math.ceil(durationMinutes \/ 30);/g' "$TMP_FILE"

# Fix 10: Add config retry limit
echo "10. Adding config retry limit..."
sed -i '/let gapi_loaded = false;/a\        let configRetries = 0;\n        const MAX_CONFIG_RETRIES = 3;' "$TMP_FILE"

# Move the temporary file to replace the original
mv "$TMP_FILE" index.html

echo "✅ All fixes applied successfully!"
echo "📁 Backup saved as: index.html.backup.$(date +%Y%m%d_%H%M%S)"
echo ""
echo "Now please:"
echo "1. Refresh your browser with Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo "2. Check if Flask is running: python app.py"
echo "3. Test the calendar sync functionality"

# Clean up temporary files
rm -f replace_function.tmp

echo ""
echo "If issues persist, check the console for any remaining errors."