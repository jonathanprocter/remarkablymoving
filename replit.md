# Overview

This is a web-based calendar generator specifically designed for reMarkable e-ink tablets. The application creates PDF calendars optimized for the reMarkable's display characteristics, with features like time slot management, Google Calendar integration, and e-ink display optimization. The tool allows users to generate custom calendar layouts that work well on reMarkable devices for productivity and planning purposes.

**reMarkable Pro PDF Export Integration (Sep 9, 2025)**:
- Integrated Python-based PDF generator using reportlab library optimized for reMarkable Pro specifications
- Replaced JavaScript/Puppeteer-based PDF generation with native Python implementation for better performance
- Implemented true reMarkable Pro dimensions: 2160x1620 pixels (landscape), 1620x2160 pixels (portrait)
- Added bidirectional hyperlinks between weekly overview and daily pages for seamless navigation
- Supports military time format (07:00-22:00) with 30-minute intervals throughout the day
- Generates complete 8-page PDF layout: 1 landscape weekly overview + 7 portrait daily views
- Direct Google Calendar integration for generating PDFs from authenticated calendar events
- Two PDF generation methods: from current calendar view data or directly from Google Calendar API

**Latest Update (Sep 2025)**: 
- Extended sync capability to load complete calendar history from 2015-2030, with optimized chunked API requests and PostgreSQL storage for comprehensive calendar template generation.
- Added server-side PDF generation using Puppeteer for reMarkable Paper Pro Move (7.3" screen) optimized planners with 8-page format (1 weekly overview + 7 daily pages)
- Optimized PDF dimensions for reMarkable Paper Pro Move: 91mm × 163mm portrait for daily pages, 163mm × 91mm landscape for weekly overview
- Reduced font sizes and adjusted layouts for the smaller 7.3" screen with 1696 × 954 pixel resolution
- **Critical Optimizations (Sep 8, 2025)**:
  - Reduced daily time slots from 30 (30-minute intervals) to 16 (hourly intervals) for better readability on 7.3" screen
  - Implemented PlannerEventManager class for bidirectional event linking between weekly and daily views
  - Optimized CSS with custom properties for consistent font sizing (4pt-6pt range)
  - Improved space allocation: time grid now uses ~50% of vertical space, priorities/goals/notes properly sized
  - Added event priority highlighting with visual indicators (high priority events show in red background)
- **Critical Fixes (Sep 8, 2025 - Evening)**:
  - Fixed page overflow issue: Weekly planner now fits on single landscape page (163mm × 91mm)
  - Resolved text truncation: Proper text sizing and ellipsis for long event titles
  - Enhanced bidirectional linking: Events sync between weekly overview (business hours 9-5) and daily views
  - Corrected layout dimensions: All pages properly sized for reMarkable Paper Pro Move specifications
  - Improved grid structure: Proper IDs for event cells enabling JavaScript event management

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Single Page Application (SPA)**: Built as a client-side web application using vanilla HTML, CSS, and JavaScript
- **Responsive Design**: Uses Tailwind CSS framework for responsive layouts and modern UI components
- **Component-Based Styling**: Leverages FontAwesome icons and custom CSS for enhanced visual elements
- **E-ink Optimization**: Custom CSS filters and styling specifically designed for e-ink display characteristics

## PDF Generation
- **Client-Side PDF Creation**: Uses jsPDF library for generating PDF documents directly in the browser
- **reMarkable Format Optimization**: Custom aspect ratios (4:3) and styling to match reMarkable tablet dimensions
- **Franklin Planner Layout**: Professional time-based grid layout following Franklin Covey methodology
- **Print-Friendly Output**: Generates PDFs optimized for e-ink displays with appropriate contrast and brightness adjustments

## Calendar System
- **Franklin Style Layout**: Professional time-based grid following Franklin Planner methodology
- **Structured Time Management**: Organized time slots (6AM-8PM) with clean event placement
- **Priority Management**: Integrated A/B/C priority sections and goal tracking areas
- **Professional Typography**: Courier New monospace font for classic planner appearance
- **Custom Date Handling**: JavaScript-based date manipulation for calendar generation

## Integration Layer
- **Google Calendar API**: Integration with Google APIs for importing calendar events
- **OAuth Authentication**: Google API authentication for accessing user calendar data
- **Real-time Sync**: Sync indicators and real-time updates from external calendar sources
- **Extended Range Sync**: Optimized 15-year historical sync (2015-2030) with chunked API requests
- **PostgreSQL Storage**: Persistent storage of calendar events and user data for offline access
- **Flexible Sync Options**: User can choose between current week or full historical range

# External Dependencies

## Frontend Libraries
- **Tailwind CSS (v2.2.19)**: CSS framework for styling and responsive design
- **FontAwesome (v6.4.0)**: Icon library for UI elements
- **jsPDF (v2.5.1)**: Client-side PDF generation library

## API Integrations
- **Google Calendar API**: For importing and syncing calendar events
- **Google APIs JavaScript Client**: For handling Google service authentication and API calls

## CDN Dependencies
- All external libraries are loaded via CDN for simplified deployment
- No build process or package management required
- Direct browser compatibility without compilation steps