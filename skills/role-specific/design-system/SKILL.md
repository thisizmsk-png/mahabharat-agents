---
name: design-system
description: "Design system skill — creates and maintains design tokens, component APIs, accessibility standards, and visual consistency."
user-invocable: true
---

# Design System

You are building or maintaining a design system — the source of truth for visual
and interaction consistency across the product.

## Design System Components

### 1. Design Tokens
- **Colors:** Primary, secondary, semantic (success, error, warning), dark/light mode
- **Typography:** Font families, sizes, weights, line heights
- **Spacing:** Scale (4px base grid: 4, 8, 12, 16, 24, 32, 48, 64)
- **Borders:** Radius, widths, styles
- **Shadows:** Elevation levels
- **Breakpoints:** Mobile, tablet, desktop, wide

### 2. Component API Design
- Props should be intuitive and consistent across components
- Use composition over configuration (children > props for complex content)
- Support `className` and `style` for escape hatches
- Include `aria-*` props for accessibility

### 3. Accessibility Standards (WCAG 2.1 AA)
- Color contrast ratio: 4.5:1 for text, 3:1 for large text
- Keyboard navigation: all interactive elements focusable and operable
- Screen reader: semantic HTML, ARIA labels, live regions
- Motion: respect `prefers-reduced-motion`

### 4. Component Documentation
```markdown
## ComponentName

### Usage
[When to use, when NOT to use]

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|

### Examples
[Code examples for common use cases]

### Accessibility
[ARIA attributes, keyboard behavior, screen reader behavior]
```

## Rules
- Every component must be accessible (WCAG 2.1 AA minimum)
- Design tokens are the ONLY source of visual values — no hardcoded colors/sizes
- Components must work in both light and dark mode
- Test visually across breakpoints before shipping
- Zero Cognitive Bias Protocol — don't choose patterns because they're trendy
