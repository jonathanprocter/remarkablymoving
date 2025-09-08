# Overview

This is a web-based calendar generator specifically designed for reMarkable e-ink tablets. The application creates PDF calendars optimized for the reMarkable's display characteristics, with features like time slot management, Google Calendar integration, and e-ink display optimization. The tool allows users to generate custom calendar layouts that work well on reMarkable devices for productivity and planning purposes.

**Latest Update (Sep 2025)**: Extended sync capability to load complete calendar history from 2015-2030, with optimized chunked API requests and PostgreSQL storage for comprehensive calendar template generation.

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
- **Print-Friendly Output**: Generates PDFs optimized for e-ink displays with appropriate contrast and brightness adjustments

## Calendar System
- **Grid-Based Layout**: CSS Grid implementation for flexible calendar layouts
- **Time Slot Management**: Configurable time slots with dotted borders for writing spaces
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