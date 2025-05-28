# PersistentDialog Component

A dialog component that prevents accidental dismissal and optionally supports form functionality.

## Features

- Prevents dismissal on backdrop click
- Disables escape key dismissal
- Optional form wrapper
- Customizable title
- Full width by default

## Props

| Prop     | Type      | Description                   |
| -------- | --------- | ----------------------------- |
| open     | boolean   | Controls dialog visibility    |
| onClose  | function  | Handler for dialog close      |
| title    | string    | Dialog title text             |
| isForm   | boolean   | Wraps content in form element |
| onSubmit | function  | Form submit handler           |
| children | ReactNode | Dialog content                |

## Usage Examples

### Basic Dialog

```javascript
<PersistentDialog
  open={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirmation"
>
  <DialogContent>Are you sure you want to proceed?</DialogContent>
  <DialogActions>
    <Button onClick={handleClose}>Cancel</Button>
    <Button onClick={handleConfirm}>Confirm</Button>
  </DialogActions>
</PersistentDialog>
```

### Form Dialog

```javascript
<PersistentDialog
  open={isOpen}
  onClose={() => setIsOpen(false)}
  title="Create User"
  isForm={true}
  onSubmit={handleSubmit}
>
  <DialogContent>
    <TextField label="Name" />
    <TextField label="Email" />
  </DialogContent>
  <DialogActions>
    <Button onClick={handleClose}>Cancel</Button>
    <Button type="submit">Submit</Button>
  </DialogActions>
</PersistentDialog>
```

## Notes

- Built on top of Material-UI's Dialog component
- Automatically handles form submission when isForm is true
- Prevents accidental dismissal for better UX
- Maintains focus within dialog for accessibility
