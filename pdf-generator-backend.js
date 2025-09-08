// pdf-generator-backend.js - Express backend for PDF generation
const express = require('express');
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;

const router = express.Router();

// Event management system for bidirectional linking
class PlannerEventManager {
  constructor() {
    this.events = new Map(); // eventId -> event object
    this.weeklyEvents = new Set(); // events visible on weekly view
    this.dailyEvents = new Map(); // date -> Set of eventIds
    this.nextId = 1;
    this.eventCounter = 0;
    this.weeklyTotal = 0;
    this.dailyCounts = {
      mon: 0, tue: 0, wed: 0, thu: 0, 
      fri: 0, sat: 0, sun: 0
    };
  }
  
  generateId() {
    return `event-${this.nextId++}`;
  }
  
  addEvent(event) {
    const eventId = this.generateId();
    event.id = eventId;
    this.events.set(eventId, event);
    
    // Add to weekly view if multi-day or important or within business hours
    const [eventHour] = (event.time || '09:00').split(':').map(Number);
    const isBusinessHour = eventHour >= 9 && eventHour <= 17;
    
    if ((event.duration > 60 || event.priority === 'high' || event.showInWeekly) && isBusinessHour) {
      this.weeklyEvents.add(eventId);
    }
    
    // Add to specific day
    const dateKey = event.dayKey || event.date.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
    if (!this.dailyEvents.has(dateKey)) {
      this.dailyEvents.set(dateKey, new Set());
    }
    this.dailyEvents.get(dateKey).add(eventId);
    
    // Update counts
    const dayAbbr = dateKey.substring(0, 3);
    if (this.dailyCounts[dayAbbr] !== undefined) {
      this.dailyCounts[dayAbbr]++;
      this.weeklyTotal++;
    }
    
    return eventId;
  }
  
  getWeeklyEvents() {
    return Array.from(this.weeklyEvents).map(id => this.events.get(id));
  }
  
  getDailyEvents(dayKey) {
    const eventIds = this.dailyEvents.get(dayKey) || new Set();
    return Array.from(eventIds).map(id => this.events.get(id));
  }
  
  getAllEvents() {
    return Array.from(this.events.values());
  }
  
  isBusinessHour(time) {
    const hour = parseInt(time.split(':')[0]);
    return hour >= 9 && hour <= 17;
  }
}

// PDF generation endpoint
router.post('/generate-planner-pdf', async (req, res) => {
  try {
    const { weekData, startDate } = req.body;
    
    // Generate HTML content
    const htmlContent = generatePlannerHTML(weekData, startDate);
    
    // Launch puppeteer with system chromium
    const browser = await puppeteer.launch({
      headless: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    });
    
    const page = await browser.newPage();
    
    // Set content
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
    
    // Generate PDF with reMarkable Pro Move dimensions
    // Optimized for 7.3" screen (91mm × 163mm)
    const pdf = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,  // Let CSS control page sizes
      displayHeaderFooter: false,
      margin: { top: '0', right: '0', bottom: '0', left: '0' }
    });
    
    await browser.close();
    
    // Set headers for file download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="planner-${startDate}.pdf"`);
    
    res.send(pdf);
  } catch (error) {
    console.error('PDF generation error:', error);
    res.status(500).json({ error: 'Failed to generate PDF' });
  }
});

// HTML template generator with event manager
function generatePlannerHTML(weekData, startDate) {
  const date = new Date(startDate);
  const weekDays = [];
  const eventManager = new PlannerEventManager();
  
  // Generate week days
  for (let i = 0; i < 7; i++) {
    const currentDate = new Date(date);
    currentDate.setDate(date.getDate() + i);
    weekDays.push({
      name: currentDate.toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase(),
      date: currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase(),
      key: currentDate.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase(),
      dateObj: currentDate
    });
  }
  
  // Process and add events to manager for bidirectional linking
  if (weekData.events) {
    Object.keys(weekData.events).forEach(dayKey => {
      const dayEvents = weekData.events[dayKey] || [];
      dayEvents.forEach(event => {
        eventManager.addEvent({
          ...event,
          dayKey,
          date: new Date(),
          priority: event.priority || (event.duration > 90 ? 'high' : 'normal'),
          showInWeekly: event.duration > 60 || event.priority === 'high'
        });
      });
    });
  }
  
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>reMarkable Planner</title>
    <style>
        ${getOptimizedCSS()}
    </style>
    <script>
        ${getBidirectionalLinkingScript()}
    </script>
</head>
<body>
    ${generateWeeklyPage(weekData, weekDays, eventManager)}
    ${generateDailyPages(weekData, weekDays, eventManager)}
</body>
</html>`;
}

function getOptimizedCSS() {
  return `
    /* reMarkable Paper Pro Move Specifications */
    :root {
      --portrait-width: 91mm;
      --portrait-height: 163mm;
      --landscape-width: 163mm;
      --landscape-height: 91mm;
      --margin: 2mm;
      
      /* Typography optimized for e-ink */
      --font-xlarge: 9pt;
      --font-large: 7pt;
      --font-medium: 6pt;
      --font-small: 5pt;
      --font-tiny: 4pt;
      
      /* Colors for e-ink display */
      --black: #000000;
      --gray: #666666;
      --light-gray: #cccccc;
      --white: #ffffff;
    }
    
    /* Page sizing for reMarkable Paper Pro Move */
    @page {
      margin: var(--margin);
    }
    
    /* First page (weekly) - landscape */
    @page :first {
      size: 163mm 91mm;
      margin: var(--margin);
    }
    
    /* Daily pages - Portrait */
    @page :not(:first) {
      size: 91mm 163mm;
      margin: var(--margin);
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    
    h1, h2, h3 {
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: 'Times', serif;
      color: #000000;
      background: #ffffff;
      -webkit-print-color-adjust: exact;
    }
    
    /* Page management */
    .page {
      page-break-after: always;
      page-break-inside: avoid;
      overflow: hidden;
    }
    
    .page:last-child {
      page-break-after: auto;
    }
    
    /* Weekly Page - Landscape */
    .weekly-page {
      width: calc(var(--landscape-width) - 2 * var(--margin));
      height: calc(var(--landscape-height) - 2 * var(--margin));
    }
    
    .weekly-container {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .weekly-header {
      height: 10mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2pt solid var(--black);
      padding: 0 2mm;
      margin-bottom: 2mm;
    }
    
    .weekly-header h1 {
      font-size: var(--font-xlarge);
      font-weight: bold;
    }
    
    .weekly-header span {
      font-size: var(--font-large);
    }
    
    .weekly-content {
      flex: 1;
      display: flex;
      gap: 3mm;
    }
    
    .weekly-grid {
      flex: 2.5;
      display: grid;
      grid-template-columns: 12mm repeat(7, 1fr);
      grid-template-rows: 5mm repeat(17, 1fr);
      border: 2pt solid var(--black);
    }
    
    .grid-cell {
      border-right: 0.5pt solid var(--black);
      border-bottom: 0.5pt solid var(--black);
      padding: 0.5mm;
      overflow: hidden;
    }
    
    .header-cell {
      background: #f0f0f0;
      font-weight: bold;
      font-size: var(--font-small);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .time-cell {
      background: #f8f8f8;
      font-weight: bold;
      font-size: var(--font-tiny);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .event-cell {
      font-size: 3pt;
      min-height: 3mm;
    }
    
    .weekly-sidebar {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2mm;
    }
    
    .tasks-section, .goals-section {
      flex: 1;
      border: 2pt solid var(--black);
      padding: 2mm;
    }
    
    .tasks-section h3, .goals-section h3 {
      font-size: var(--font-medium);
      font-weight: bold;
      margin-bottom: 2mm;
      border-bottom: 1pt solid var(--black);
      padding-bottom: 1mm;
    }
    
    .task-item, .goal-item {
      font-size: var(--font-small);
      margin-bottom: 1mm;
      line-height: 1.3;
    }
    
    /* Remove old footer styles */
    .weekly-footer, .footer-section, .footer-title,
    .checkbox-item, .checkbox {
      display: none;
    }
    
    .weekly-footer {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 2mm;
      margin-top: 2mm;
      height: 15mm;
    }
    
    .footer-section {
      border: 1pt solid #000;
      padding: 1mm;
      font-size: 5pt;
    }
    
    .footer-title {
      font-weight: bold;
      font-size: 6pt;
      border-bottom: 0.5pt solid #000;
      margin-bottom: 1mm;
    }
    
    .footer-section {
      border: 0.5pt solid #000;
      padding: 1mm;
    }
    
    .footer-title {
      font-weight: bold;
      font-size: 7pt;  /* Smaller for Pro Move */
      border-bottom: 0.5pt solid #000;
      padding-bottom: 1mm;
      margin-bottom: 1mm;
      text-align: center;
    }
    
    .checkbox-item {
      display: flex;
      align-items: center;
      margin: 0.75mm 0;
      font-size: 6pt;  /* Smaller for Pro Move */
    }
    
    .checkbox {
      width: 2mm;
      height: 2mm;
      border: 0.5pt solid #000;
      margin-right: 1mm;
      flex-shrink: 0;
      background: #fff;
    }
    
    /* Daily Pages - Portrait */
    @page :not(:first) {
      size: 91mm 163mm;
      margin: var(--margin);
    }
    
    .daily-page {
      width: calc(var(--portrait-width) - 2 * var(--margin));
      height: calc(var(--portrait-height) - 2 * var(--margin));
    }
    
    .daily-container {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .daily-main {
      height: 105mm;
      border: 2pt solid var(--black);
      margin-bottom: 1mm;
    }
    
    .daily-header {
      height: 8mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2pt solid var(--black);
      padding: 0 1mm;
      margin-bottom: 1mm;
    }
    
    .daily-title {
      font-size: var(--font-large);
      font-weight: bold;
    }
    
    .daily-date {
      font-size: var(--font-medium);
    }
    
    .time-section {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .time-row {
      flex: 1;
      display: flex;
      border-bottom: 0.5pt solid var(--light-gray);
      min-height: 4mm;
    }
    
    .time-row:last-child {
      border-bottom: none;
    }
    
    .time-label {
      width: 12mm;
      background: #f8f8f8;
      border-right: 2pt solid var(--black);
      font-size: var(--font-small);
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .time-space {
      flex: 1;
      padding: 0.5mm;
      font-size: var(--font-small);
    }
    
    .daily-bottom {
      height: 44mm;
      display: flex;
      flex-direction: column;
      gap: 1mm;
    }
    
    .daily-event {
      background: #000;
      color: #fff;
      padding: 0.5mm 1mm;
      margin: 0.25mm 0;
      border-radius: 0.5px;
      font-size: 6pt;  /* Smaller for Pro Move */
      line-height: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .sidebar-section {
      border: 0.5pt solid #000;
      margin-bottom: 2mm;
      padding: 1mm;
    }
    
    .sidebar-title {
      font-weight: bold;
      font-size: 6pt;  /* Smaller for Pro Move */
      border-bottom: 0.5pt solid #000;
      padding-bottom: 0.5mm;
      margin-bottom: 1mm;
      text-align: center;
    }
    
    .goal-line {
      border-bottom: 0.5pt solid #ccc;
      margin: 1mm 0;
      height: 3mm;
    }
    
    .event-summary {
      font-size: 5pt;  /* Smaller for Pro Move */
      line-height: 1.1;
      margin: 0.5mm 0;
    }
    
    .status-text {
      font-size: 6pt;  /* Smaller for Pro Move */
      margin: 0.5mm 0;
    }
    
    .priorities-section {
      height: 18mm;
      border: 2pt solid var(--black);
      padding: 2mm;
    }
    
    .section-title {
      font-size: var(--font-medium);
      font-weight: bold;
      margin-bottom: 2mm;
    }
    
    .priority-line {
      display: flex;
      align-items: center;
      margin-bottom: 1mm;
      font-size: var(--font-small);
    }
    
    .write-line {
      flex: 1;
      height: 1pt;
      background: var(--light-gray);
      margin-left: 2mm;
    }
    
    .bottom-sections {
      height: 22mm;
      display: flex;
      gap: 2mm;
    }
    
    .goals-box, .notes-box {
      flex: 1;
      border: 2pt solid var(--black);
      padding: 2mm;
    }
    
    .write-area {
      height: calc(100% - 8mm);
      border-bottom: 1pt solid var(--light-gray);
    }
    
    .status-line {
      height: 6mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--font-tiny);
      color: var(--gray);
      padding: 0 1mm;
    }
    
    /* High contrast mode for better e-ink visibility */
    .high-contrast {
      filter: contrast(1.2);
    }
    
    /* Ensure proper page breaks */
    .page-break {
      page-break-before: always;
    }
  `;
}

function generateWeeklyPage(weekData, weekDays, eventManager) {
  const timeSlots = generateTimeSlots(9, 17, 30); // 9 AM to 5 PM business hours with 30-min intervals (17 slots)
  
  return `
    <div class="page weekly-page">
        <div class="weekly-container">
            <div class="weekly-header">
                <h1>WEEKLY PLANNER</h1>
                <span>WEEK OF ${weekDays[0].date}</span>
            </div>
            
            <div class="weekly-content">
                <div class="weekly-grid">
                    <div class="grid-cell header-cell">TIME</div>
                    ${weekDays.map(day => `<div class="grid-cell header-cell">${day.name.substring(0, 3).toUpperCase()}</div>`).join('')}
                    
                    ${timeSlots.map(time => {
                      const timeStr = time.replace(':', '');
                      return `
                        <div class="grid-cell time-cell">${time}</div>
                        ${weekDays.map(day => `
                            <div class="grid-cell event-cell" id="w-${day.key.substring(0, 3)}-${timeStr}" data-day="${day.key.substring(0, 3)}" data-time="${time}">
                                ${getWeeklyEventsForTimeSlot(weekData, day.key, time)}
                            </div>
                        `).join('')}
                      `;
                    }).join('')}
                </div>
                
                <div class="weekly-sidebar">
                    <div class="tasks-section">
                        <h3>PRIORITY TASKS</h3>
                        <div class="task-list">
                            ${(weekData.priorityTasks || ['Follow up on client contracts', 'Prepare quarterly review materials', 'Update team schedules', 'Review project deliverables', 'Schedule follow-up meetings']).slice(0, 5).map((task, i) => 
                                `<div class="task-item" id="task-${i+1}">${task}</div>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="goals-section">
                        <h3>WEEKLY GOALS</h3>
                        <div class="goal-list">
                            ${(weekData.weeklyGoals || ['Complete all scheduled appointments', 'Review and update project timelines', 'Prepare for upcoming presentations']).slice(0, 3).map(goal => 
                                `<div class="goal-item">${goal}</div>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function generateDailyPages(weekData, weekDays, eventManager) {
  return weekDays.map(day => generateDailyPage(weekData, day, eventManager)).join('');
}

function generateDailyPage(weekData, day, eventManager) {
  const timeSlots = generateTimeSlots(7, 22, 30); // 7 AM to 10 PM, 30-minute intervals (31 slots)
  const dayEvents = eventManager ? eventManager.getDailyEvents(day.key) : (weekData.events?.[day.key] || []);
  const dayAbbr = day.key.substring(0, 3);
  
  return `
    <div class="page daily-page" data-date="${day.dateObj.toISOString().split('T')[0]}" data-day="${dayAbbr}">
        <div class="daily-container">
            <div class="daily-header">
                <span class="daily-title">DAILY PLANNER - ${day.name}</span>
                <span class="daily-date">${day.date}</span>
            </div>
            
            <div class="daily-main">
                <div class="time-section">
                    ${timeSlots.map(time => {
                      const timeStr = time.replace(':', '');
                      return `
                        <div class="time-row">
                            <div class="time-label">${time}</div>
                            <div class="time-space" id="d-${dayAbbr}-${timeStr}" data-time="${time}" data-day="${dayAbbr}">
                                ${getDailyEventsForTime(dayEvents, time)}
                            </div>
                        </div>
                      `;
                    }).join('')}
                </div>
            </div>
            
            <div class="daily-bottom">
                <div class="priorities-section">
                    <div class="section-title">PRIORITIES</div>
                    <div class="priority-line">A) <div class="write-line"></div></div>
                    <div class="priority-line">B) <div class="write-line"></div></div>
                    <div class="priority-line">C) <div class="write-line"></div></div>
                </div>
                
                <div class="bottom-sections">
                    <div class="goals-box">
                        <div class="section-title">DAILY GOALS</div>
                        <div class="write-area"></div>
                    </div>
                    
                    <div class="notes-box">
                        <div class="section-title">NOTES</div>
                        <div class="write-area"></div>
                    </div>
                </div>
                
                <div class="status-line">
                    <span class="event-count" id="count-${dayAbbr}">${dayEvents.length} events</span>
                    <span class="week-total">Week: <span id="total-events">${getTotalEventCount(weekData)}</span> total</span>
                </div>
            </div>
        </div>
    </div>`;
}

// Utility functions
function generateTimeSlots(startHour, endHour, intervalMinutes) {
  const slots = [];
  for (let hour = startHour; hour <= endHour; hour++) {
    for (let minute = 0; minute < 60; minute += intervalMinutes) {
      if (hour === endHour && minute > 0) break;
      slots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
  }
  return slots;
}

function getWeeklyEventsForTimeSlot(weekData, dayKey, timeSlot) {
  const dayEvents = weekData.events?.[dayKey] || [];
  const [hour, minute] = timeSlot.split(':').map(Number);
  const slotTime = hour * 60 + minute;
  const slotEndTime = slotTime + 30; // 30-minute slot
  
  return dayEvents
    .filter(event => {
      const [eventHour, eventMinute] = (event.time || '09:00').split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      const eventEndTime = eventStartTime + (event.duration || 60);
      
      // Show event if it overlaps with this 30-min slot and is within business hours
      return (eventStartTime < slotEndTime && eventEndTime > slotTime) && 
             (eventHour >= 9 && eventHour <= 17);
    })
    .map(event => {
      const truncatedTitle = event.title.length > 8 ? event.title.substring(0, 8) + '...' : event.title;
      const bgColor = event.priority === 'high' ? '#e0e0e0' : '';
      return truncatedTitle ? `<span style="background-color: ${bgColor};">${truncatedTitle}</span>` : '';
    })
    .join(' ');
}

function getDailyEventsForTime(events, timeSlot) {
  const [hour, minute] = timeSlot.split(':').map(Number);
  const slotTime = hour * 60 + minute;
  const slotEndTime = slotTime + 30; // 30-minute slot
  
  return events
    .filter(event => {
      const [eventHour, eventMinute] = (event.time || '09:00').split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      const eventEndTime = eventStartTime + (event.duration || 60);
      // Show events that start in or overlap with this 30-min slot
      return (eventStartTime >= slotTime && eventStartTime < slotEndTime) ||
             (eventStartTime < slotTime && eventEndTime > slotTime);
    })
    .map(event => {
      const bgColor = event.priority === 'high' ? '#f0f0f0' : '';
      return event.title ? `<span style="background-color: ${bgColor};">${event.title}</span>` : '';
    })
    .join(' ');
}

function getTotalEventCount(weekData) {
  if (!weekData.events) return 0;
  return Object.values(weekData.events).reduce((total, dayEvents) => total + dayEvents.length, 0);
}

function getBidirectionalLinkingScript() {
  return `
    class RemarkablePlanner {
      constructor() {
        this.events = new Map();
        this.dailyCounts = { mon: 0, tue: 0, wed: 0, thu: 0, fri: 0, sat: 0, sun: 0 };
        this.totalEvents = 0;
        this.init();
      }
      
      init() {
        // Initialize event listeners and setup
        document.addEventListener('DOMContentLoaded', () => {
          this.updateAllCounts();
        });
      }
      
      addEvent(day, hour, title, priority = 'normal') {
        const eventId = \`\${day}-\${hour}-\${Date.now()}\`;
        const event = {
          id: eventId,
          day,
          hour,
          title,
          priority,
          showInWeekly: this.shouldShowInWeekly(hour, priority)
        };
        
        this.events.set(eventId, event);
        
        // Update daily view
        this.updateDailyView(event);
        
        // Update weekly view if applicable
        if (event.showInWeekly) {
          this.updateWeeklyView(event);
        }
        
        // Update counters
        this.updateCounts(day);
        
        return eventId;
      }
      
      shouldShowInWeekly(hour, priority) {
        // Show in weekly if business hours (9-17) or high priority
        const h = parseInt(hour);
        return (h >= 9 && h <= 17) || priority === 'high';
      }
      
      updateDailyView(event) {
        const dailyCell = document.getElementById(\`d-\${event.day}-\${event.hour.padStart(2, '0')}\`);
        if (dailyCell) {
          dailyCell.textContent = event.title;
          dailyCell.style.backgroundColor = event.priority === 'high' ? '#ffeeee' : '#f0f0f0';
        }
      }
      
      updateWeeklyView(event) {
        const weeklyCell = document.getElementById(\`w-\${event.day}-\${event.hour.padStart(2, '0')}\`);
        if (weeklyCell) {
          // Truncate title for weekly view
          const shortTitle = event.title.length > 6 ? 
            event.title.substring(0, 6) + '...' : event.title;
          weeklyCell.textContent = shortTitle;
          weeklyCell.style.backgroundColor = event.priority === 'high' ? '#ffeeee' : '#e8e8e8';
        }
      }
      
      updateCounts(day) {
        this.dailyCounts[day]++;
        this.totalEvents++;
        
        // Update daily count display
        const countElement = document.getElementById(\`count-\${day}\`);
        if (countElement) {
          countElement.textContent = \`\${this.dailyCounts[day]} events\`;
        }
        
        // Update total count across all pages
        document.querySelectorAll('#total-events').forEach(el => {
          el.textContent = this.totalEvents;
        });
      }
      
      updateAllCounts() {
        // Initialize all counts to zero
        Object.keys(this.dailyCounts).forEach(day => {
          const countElement = document.getElementById(\`count-\${day}\`);
          if (countElement) {
            countElement.textContent = \`\${this.dailyCounts[day]} events\`;
          }
        });
        
        document.querySelectorAll('#total-events').forEach(el => {
          el.textContent = this.totalEvents;
        });
      }
      
      // Demo function to add sample events
      addSampleEvents() {
        this.addEvent('mon', '09', 'Team Meeting', 'high');
        this.addEvent('mon', '14', 'Client Call', 'normal');
        this.addEvent('tue', '10', 'Project Review', 'high');
        this.addEvent('wed', '15', 'Design Session', 'normal');
        this.addEvent('fri', '11', 'Sprint Planning', 'high');
      }
    }
    
    // Initialize planner when document loads
    if (typeof document !== 'undefined') {
      document.addEventListener('DOMContentLoaded', () => {
        const planner = new RemarkablePlanner();
        // For testing - uncomment to add sample events
        // planner.addSampleEvents();
      });
    }
  `;
}

module.exports = router;