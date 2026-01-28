# Dashboard - Dashboard Module

![Dashboard Icon](static/Dashboard.png)

A customizable dashboard system for displaying and organizing objects with flexible grouping options.

## Description

The `Dashboard` module provides a dashboard interface for the osysHome platform. It enables users to view objects, organize them by class or custom properties, and customize their dashboard experience.

## Main Features

- ✅ **Object Display**: Display objects with their templates
- ✅ **Flexible Grouping**: Group by class, custom properties, or no grouping
- ✅ **Custom Groups**: Create custom grouping rules
- ✅ **Value Substitutions**: Customize group titles with value substitutions
- ✅ **User Preferences**: Save user-specific dashboard preferences
- ✅ **Real-Time Updates**: WebSocket updates for object changes

## Grouping Options

### No Grouping
- Display all objects in a single view
- Simple flat list

### By Class
- Group objects by their class hierarchy
- Show class descriptions
- Hierarchical organization

### Custom Groups
- Group by any object property
- Support for nested properties (object.property)
- Value substitutions for display
- Show/hide undefined values

## Admin Panel

The module provides configuration interface:

### Settings
- **Enable Class Grouping**: Toggle class-based grouping
- **Hide Welcome Message**: Hide welcome message on dashboard
- **Hide No Grouping Option**: Hide "No Grouping" option
- **Custom Groups**: Configure custom grouping rules

### Custom Group Configuration
- **Group Name**: Display name for the group
- **Icon**: Font Awesome icon for the group
- **Property Name**: Property to group by
- **Object Property**: Nested property (optional)
- **Show Undefined**: Show objects without property value
- **Value Substitutions**: Map values to display names

## Usage

### Viewing Dashboard

1. Navigate to Dashboard (`/Dashboard/index`)
2. Select grouping option from dropdown
3. View objects organized by selected grouping
4. Group preference saved per user

### Configuring Custom Groups

1. Navigate to Dashboard admin panel
2. Add custom group
3. Configure grouping rules
4. Set value substitutions
5. Save configuration

## Technical Details

- **Object Rendering**: Uses object templates for display
- **Grouping Logic**: Flexible property-based grouping
- **User Preferences**: Stored in user object properties
- **WebSocket**: Real-time object updates
- **API**: JSON API for dashboard data

## Version

Current version: **1.0**

## Category

App

## Author

Eraser

## Requirements

- Flask
- Flask-Login
- osysHome core system

## License

See the main osysHome project license

