# Dashboard - documentation

`Dashboard` is the home page with object cards and switchable grouping modes.

[Russian version](index.ru.md)

## Where to find it

- User page: `/index`
- Admin page: `Administration -> Dashboard`

## Main features

- displays object cards;
- lets you switch grouping mode;
- remembers the selected mode per user;
- updates cards and groups in real time.

> [!IMPORTANT]
> Dashboard only shows objects that have a display template (`render` / template).

## User interface (`/index`)

This is what a regular user sees on the Dashboard page.

### Page elements

- ribbon of grouping buttons (if more than one mode is available);
- group blocks with a title and object count;
- object cards inside groups;
- collapse / expand groups.

### How to use

1. Open `/index`.
2. Choose a mode in the top ribbon.
3. Browse object cards in that mode.
4. Collapse groups you use less often.

### What is remembered

- the selected grouping mode is stored per user;
- collapsed/expanded state is stored in the browser (`localStorage`).

### Important limitations

- without a template / `render`, an object is not shown;
- if an administrator disables a mode, the first available mode is chosen automatically.

## Admin settings

Settings under `Administration -> Dashboard`. UI labels below match `plugins/Dashboard/translations/en.json`.

### General settings

| Field | What it does |
| --- | --- |
| `Enable Grouping by Class` | Adds class-based grouping as an available mode |
| `Hide Welcome Message` | Hides the welcome banner on `/index` |
| `Hide "No Grouping" Option` | Removes the ungrouped (flat list) mode from choices |

### Custom groups (`Custom Grouping Configurations`)

| Field | Purpose | Example |
| --- | --- | --- |
| `Group Name` | Label for this grouping mode in the UI | `Rooms` |
| `Icon` | Icon CSS class | `fas fa-door-open` |
| `Property Name` | Object property used for grouping | `room` |
| `Object Property` | Property on the referenced object (when the value is another object name) | `name` |
| `Value Substitutions` | Map raw values to group titles | `0-Off,1-On` |
| `Show objects with undefined property value` | Put objects with no value in the `Undefined` group | On / Off |

### Quick setup for a new group

1. Click `Add Group`.
2. Fill at least `Group Name` and `Property Name`.
3. Optionally set `Icon`, `Object Property`, and `Value Substitutions`.
4. Click `Save`.

## Grouping and display rules

How Dashboard builds groups.

### 1. No grouping (`none`)

All rendered objects appear in one flat list.

### 2. By class (`class`)

Objects are grouped by the first parent (class).
The group title comes from the class description or its name.

### 3. Custom grouping (`custom`)

Grouping uses the `Property Name` field.

- if `Object Property` is empty: the property value on the current object is used;
- if `Object Property` is set: the `Property Name` value is treated as another object's name, and that object's property is read.

### Which objects appear

An object is included only when `obj.render()` returns a template.

### Empty property values

If the property has no value:

- with `Show objects with undefined property value` enabled: the object goes into the `Undefined` group;
- with it off: the object is hidden from the current view.

### Title substitution (`Value Substitutions`)

Format:

```text
key-value,key-value
```

Example:

```text
0-Off,1-On
```

## Real-time behaviour

Dashboard can refresh without a full page reload.

### What updates automatically

- card content when an object changes;
- moving an object between groups when a grouping property changes;
- socket subscriptions to objects and properties when you switch modes.

### How the client works

- subscribes to objects and properties via the socket;
- after a group change, data is refreshed through a JSON endpoint;
- card HTML is updated with a safe DOM update path.

### Caveats

- if `Object Property` is used, an extra request may be needed to compute the new group;
- on refresh failure, the page may fall back to a full reload.

## Troubleshooting

### Expected objects are missing

Check:

- the object has a template / `render`;
- the object exists in `objects_storage`;
- the active grouping mode does not filter it out.

### A grouping mode does not appear

Check:

- the group was saved under `Administration -> Dashboard`;
- `Group Name` and `Property Name` are filled in;
- modes are not hidden (`Hide "No Grouping" Option`, `Enable Grouping by Class` off if you rely on class mode).

### Object does not land in a custom group

Check:

- `Property Name` is correct;
- `Object Property` is correct when following a reference to another object;
- the property value is not empty;
- whether `Show objects with undefined property value` should apply.

### Group titles look like raw values

Add `Value Substitutions`, for example:

```text
0-Off,1-On
```

### UI did not change after editing settings

- click `Save` in the admin UI;
- switch grouping on `/index`;
- hard refresh the browser;
- check Dashboard logs if the form shows validation errors.

## Related files

- `plugins/Dashboard/__init__.py`
- `plugins/Dashboard/templates/index.html`
- `plugins/Dashboard/templates/dashboard.html`
- `plugins/Dashboard/forms/SettingForms.py`
- `plugins/Dashboard/translations/*.json`
