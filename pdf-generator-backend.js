// pdf-generator-backend.js - Express backend for PDF generation
const express = require('express');
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;

const router = express.Router();

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
    // Let CSS @page rules control individual page sizes
    const pdf = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,
      margin: {
        top: '0mm',
        right: '0mm',
        bottom: '0mm',
        left: '0mm'
      }
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

// HTML template generator
function generatePlannerHTML(weekData, startDate) {
  const date = new Date(startDate);
  const weekDays = [];
  
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
  
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>reMarkable Planner</title>
    <style>
        ${getOptimizedCSS()}
    </style>
</head>
<body>
    ${generateWeeklyPage(weekData, weekDays)}
    ${generateDailyPages(weekData, weekDays)}
</body>
</html>`;
}

function getOptimizedCSS() {
  return `
    /* reMarkable Paper Pro Move E-ink Optimized Styles (7.3" screen) */
    @page {
      margin: 0;
      size: 91mm 163mm;  /* Portrait for daily pages - Pro Move dimensions */
    }
    
    /* Weekly page - landscape orientation for narrow screen */
    @page :first {
      size: 163mm 91mm;  /* Landscape for weekly overview - Pro Move dimensions */
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    
    body {
      font-family: 'Courier New', 'Liberation Mono', monospace;
      font-size: 7pt;  /* Smaller font for 7.3" screen */
      line-height: 1.1;
      color: #000;
      background: #fff;
    }
    
    /* Weekly Layout - Landscape for reMarkable Paper Pro Move (7.3" screen) */
    .weekly-page {
      width: 163mm;  /* Pro Move landscape width */
      height: 91mm;   /* Pro Move landscape height */
      padding: 4mm;   /* Reduced padding for small screen */
      page-break-after: always;
      display: flex;
      flex-direction: column;
    }
    
    .weekly-header {
      text-align: center;
      border-bottom: 1pt solid #000;
      padding-bottom: 2mm;
      margin-bottom: 2mm;
    }
    
    .weekly-title {
      font-size: 10pt;  /* Reduced for small screen */
      font-weight: bold;
      letter-spacing: 0.5px;
    }
    
    .weekly-subtitle {
      font-size: 8pt;  /* Reduced for small screen */
      margin-top: 1mm;
    }
    
    .weekly-grid {
      flex: 1;
      display: grid;
      grid-template-columns: 25px repeat(7, 1fr);  /* Narrower time column for small screen */
      border: 0.5pt solid #000;
      max-height: 65mm;  /* Adjusted for Pro Move screen height */
    }
    
    .time-slot, .day-header, .grid-cell {
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #000;
      padding: 0.5px 1px;
      font-size: 6pt;  /* Smaller for narrow screen */
      overflow: hidden;
    }
    
    .day-header {
      font-weight: bold;
      text-align: center;
      background: #000;
      color: #fff;
      padding: 1px;
      font-size: 7pt;  /* Smaller for narrow screen */
    }
    
    .time-slot {
      font-weight: bold;
      text-align: center;
      background: #f0f0f0;
      writing-mode: horizontal-tb;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .grid-cell {
      position: relative;
      min-height: 5mm;  /* Reduced for small screen */
      vertical-align: top;
    }
    
    .weekly-event {
      background: #000;
      color: #fff;
      padding: 0.5px 1px;
      margin: 0.25px;
      font-size: 5pt;  /* Very small for narrow cells */
      border-radius: 0.5px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1;
      display: block;
      width: calc(100% - 2px);
    }
    
    .weekly-footer {
      margin-top: 2mm;
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 2mm;
      height: 15mm;  /* Much smaller for Pro Move */
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
    
    /* Daily Layout - Portrait for reMarkable Paper Pro Move (7.3" screen) */
    .daily-page {
      width: 91mm;   /* Pro Move portrait width */
      height: 163mm;  /* Pro Move portrait height */
      padding: 3mm;   /* Minimal padding for small screen */
      page-break-before: always;
      page-break-after: always;
      display: flex;
      margin: 0 auto;
      box-sizing: border-box;
    }
    
    .daily-main {
      flex: 1;
      margin-right: 2mm;
    }
    
    .daily-sidebar {
      width: 25mm;  /* Narrower sidebar for small screen */
      border-left: 0.5pt solid #000;
      padding-left: 1mm;
    }
    
    .daily-header {
      border-bottom: 1pt solid #000;
      padding-bottom: 1mm;
      margin-bottom: 2mm;
    }
    
    .daily-title {
      font-size: 8pt;  /* Smaller for Pro Move */
      font-weight: bold;
      letter-spacing: 0.3px;
    }
    
    .daily-subtitle {
      font-size: 6pt;  /* Smaller for Pro Move */
      margin-top: 1mm;
      color: #333;
    }
    
    .schedule-grid {
      display: grid;
      grid-template-columns: 18mm 1fr;  /* Narrower time column */
      border-top: 0.5pt solid #000;
    }
    
    .time-label {
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #000;
      padding: 0.5mm;
      font-size: 6pt;  /* Smaller for Pro Move */
      text-align: center;
      background: #f5f5f5;
      font-weight: bold;
    }
    
    .time-content {
      border-bottom: 0.5pt solid #000;
      padding: 0.5mm 1mm;
      min-height: 7.5mm;  /* Reduced height for small screen */
      position: relative;
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
      margin: 0.5mm 0;
      height: 2mm;
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

function generateWeeklyPage(weekData, weekDays) {
  const timeSlots = generateTimeSlots(7, 22, 60); // 7 AM to 10 PM, hourly
  
  return `
    <div class="weekly-page">
        <div class="weekly-header">
            <div class="weekly-title">WEEKLY PLANNER</div>
            <div class="weekly-subtitle">WEEK OF ${weekDays[0].date}</div>
        </div>
        
        <div class="weekly-grid">
            <div class="time-slot">TIME</div>
            ${weekDays.map(day => `<div class="day-header">${day.name.substring(0, 3)}</div>`).join('')}
            
            ${timeSlots.map(time => `
                <div class="time-slot">${time}</div>
                ${weekDays.map(day => `
                    <div class="grid-cell">
                        ${getWeeklyEventsForTimeSlot(weekData, day.key, time)}
                    </div>
                `).join('')}
            `).join('')}
        </div>
        
        <div class="weekly-footer">
            <div class="footer-section">
                <div class="footer-title">PRIORITY TASKS</div>
                ${(weekData.priorityTasks || []).slice(0, 5).map(task => 
                    `<div class="checkbox-item"><div class="checkbox"></div>${task}</div>`
                ).join('')}
                ${Array(Math.max(0, 5 - (weekData.priorityTasks || []).length)).fill().map(() => 
                    `<div class="checkbox-item"><div class="checkbox"></div><div class="goal-line" style="flex: 1;"></div></div>`
                ).join('')}
            </div>
            <div class="footer-section">
                <div class="footer-title">WEEKLY GOALS</div>
                ${(weekData.weeklyGoals || []).slice(0, 3).map(goal => 
                    `<div style="margin: 0.5mm 0; font-size: 6pt;">${goal}</div>`
                ).join('')}
                ${Array(Math.max(0, 4 - (weekData.weeklyGoals || []).length)).fill().map(() => '<div class="goal-line"></div>').join('')}
            </div>
            <div class="footer-section">
                <div class="footer-title">STATUS</div>
                <div class="status-text">${getTotalEventCount(weekData)} events this week</div>
                <div class="status-text">✓ Synced successfully</div>
                <div class="status-text">${new Date().toLocaleDateString()}</div>
                <div class="goal-line"></div>
                <div class="goal-line"></div>
            </div>
        </div>
    </div>`;
}

function generateDailyPages(weekData, weekDays) {
  return weekDays.map(day => generateDailyPage(weekData, day)).join('');
}

function generateDailyPage(weekData, day) {
  const timeSlots = generateTimeSlots(7, 22, 30); // 7 AM to 10 PM, 30-minute intervals
  const dayEvents = weekData.events?.[day.key] || [];
  
  return `
    <div class="daily-page">
        <div class="daily-main">
            <div class="daily-header">
                <div class="daily-title">DAILY PLANNER - ${day.name}</div>
                <div class="daily-subtitle">${day.date} | APPOINTMENTS & TASKS</div>
            </div>
            
            <div class="schedule-grid">
                ${timeSlots.map(time => `
                    <div class="time-label">${time}</div>
                    <div class="time-content">
                        ${getDailyEventsForTime(dayEvents, time)}
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="daily-sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">DAILY GOALS</div>
                ${Array(4).fill().map(() => 
                    `<div class="checkbox-item"><div class="checkbox"></div><div class="goal-line" style="flex: 1;"></div></div>`
                ).join('')}
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">PRIORITIES</div>
                <div style="margin: 2mm 0; font-size: 9px;">A) <div class="goal-line" style="display: inline-block; width: 75%;"></div></div>
                <div style="margin: 2mm 0; font-size: 9px;">B) <div class="goal-line" style="display: inline-block; width: 75%;"></div></div>
                <div style="margin: 2mm 0; font-size: 9px;">C) <div class="goal-line" style="display: inline-block; width: 75%;"></div></div>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">NOTES</div>
                <div class="status-text">${dayEvents.length} events scheduled</div>
                <div class="status-text">${getTotalEventCount(weekData)} total synced</div>
                ${Array(6).fill().map(() => '<div class="goal-line"></div>').join('')}
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">TODAY'S EVENTS</div>
                ${dayEvents.slice(0, 6).map(event => 
                    `<div class="event-summary">${event.time} ${event.title.substring(0, 20)}${event.title.length > 20 ? '...' : ''}</div>`
                ).join('')}
                ${dayEvents.length > 6 ? `<div class="event-summary">... +${dayEvents.length - 6} more</div>` : ''}
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
  const slotEndTime = slotTime + 60; // Full hour slot
  
  return dayEvents
    .filter(event => {
      const [eventHour, eventMinute] = event.time.split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      const eventEndTime = eventStartTime + (event.duration || 60);
      
      // Show event if it overlaps with this hour slot
      return (eventStartTime < slotEndTime && eventEndTime > slotTime);
    })
    .map(event => `<div class="weekly-event">${event.title}</div>`)
    .join('');
}

function getDailyEventsForTime(events, timeSlot) {
  const [hour, minute] = timeSlot.split(':').map(Number);
  const slotTime = hour * 60 + minute;
  
  return events
    .filter(event => {
      const [eventHour, eventMinute] = event.time.split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      return eventStartTime === slotTime;
    })
    .map(event => `<div class="daily-event">${event.title}</div>`)
    .join('');
}

function getTotalEventCount(weekData) {
  if (!weekData.events) return 0;
  return Object.values(weekData.events).reduce((total, dayEvents) => total + dayEvents.length, 0);
}

module.exports = router;