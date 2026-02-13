# SOP Management System - Problem Statement & Wireframe Requirements

## Problem Statement

### What Are SOPs and Why Do They Matter?

Standard Operating Procedures (SOPs) are step-by-step instructions that tell employees exactly how to do their work correctly and safely. Think of them as recipe books for business processes - they ensure everyone follows the same method, reducing errors and maintaining quality.

**Example**: A factory worker needs to know the exact steps to safely operate a machine. A call center agent needs the procedure for handling customer complaints. A hospital nurse needs the protocol for patient discharge.

### The Current Problems

Right now, most organizations struggle with five major issues when managing their SOPs:

#### 1. **"I Can't Find It When I Need It"**
**The Problem**: Employees need SOPs while they're working - on the factory floor, at a customer site, or from home. But SOPs are often stored in:
- Separate systems that require different passwords
- Network drives that aren't accessible from mobile devices
- Email attachments that get lost
- Paper binders that are outdated

**Real Impact**: A worker on the factory floor can't access the safety procedure on their phone. They either guess what to do (risky!) or stop work to find a computer (inefficient!).

#### 2. **"Which Version Is Correct?"**
**The Problem**: SOPs get updated frequently, but old versions keep circulating. Employees end up with:
- Multiple versions of the same SOP (which one is current?)
- Different versions for different roles or locations (hard to know which applies to you)
- Outdated procedures that cause mistakes

**Real Impact**: Employee A follows Version 2.0, Employee B follows Version 3.0, and Employee C follows Version 1.5. They all think they're doing it right, but they're doing different things!

#### 3. **"Nobody Told Me It Changed"**
**The Problem**: When SOPs are updated:
- Policy owners forget to notify everyone
- Notifications get lost in email
- It's unclear which changes are important enough to announce
- Employees don't know what changed or why

**Real Impact**: A critical safety procedure was updated last month, but half the team is still following the old (unsafe) version because they never got notified.

#### 4. **"How Do We Prove Compliance?"**
**The Problem**: Organizations need to prove to auditors (like ISO certification bodies) that:
- Employees have read the required SOPs
- Employees understand the procedures
- The organization is managing SOPs properly

**Current Reality**: No easy way to track who read what, when they read it, or if they understood it. Audits become stressful guessing games.

#### 5. **"Who's Responsible for This?"**
**The Problem**: SOPs are owned by different people across the organization:
- When someone leaves, their SOPs get forgotten
- When a team owns an SOP, nobody feels personally responsible
- Review deadlines get missed
- Updates pile up and never get done

**Real Impact**: An important SOP hasn't been updated in 3 years because the original owner left, and nobody knows who should update it now.

### What We Need

A system that solves all these problems by:
- Making SOPs easy to find and access from anywhere, on any device
- Keeping only the current, correct version visible to each employee
- Automatically notifying the right people when things change
- Tracking who read what and proving compliance automatically
- Making it clear who owns each SOP and when it needs updating

## Solution Requirements

### How We'll Solve These Problems

#### 1. **One Place for Everything**
- All SOPs in one central library (no more hunting through different systems)
- Accessible 24/7 from any device (phone, tablet, computer)
- Smart search that finds what you need quickly
- Shows you only the SOPs relevant to your role, location, and language

#### 2. **Always the Right Version**
- System automatically tracks versions (no more confusion)
- You always see the current version for your role
- Easy to see what changed between versions
- Old versions archived but accessible for reference

#### 3. **Automatic Updates & Notifications**
- System automatically notifies the right people when SOPs change
- You see what changed and why
- Policy owners get reminders when reviews are due
- Workflows guide the update process step-by-step

#### 4. **Prove Compliance Easily**
- System tracks when you read each SOP
- Optional quizzes to verify understanding
- Dashboards show your completion status
- Managers can see their team's compliance at a glance
- Reports ready for auditors with one click

#### 5. **Clear Ownership & Maintenance**
- Every SOP has a clear owner
- System sends automatic reminders for reviews
- Easy to see which SOPs need attention
- When someone leaves, ownership transfers smoothly

### Specific Features Required (From SOP App Flow)

- **Single Sign-On (O365/AD)**: Seamless authentication using existing credentials
- **Flowchart Designer Tool**: Integrated tool for creating visual process diagrams within SOPs
- **Permission & Folder Management**: Set expiration times, permissions, and organize SOPs in folders/subfolders
- **User Definition**: Specify which users (internal/external) can view each SOP
- **Multi-User Review & Approval**: Support for multiple reviewers and approvers
- **Auto-Numbering Version Control**: Automatic version numbering when SOPs are approved
- **E-Signature**: Digital signature capability for approval and sign-off
- **Notification System**: Automated notifications between Process Champions, Process Owners, and Users
- **Feedback Loop**: Ability to provide feedback/remarks and route SOPs back for updates

### Integrations
- **O365/AD**: SSO, user profile integration, Microsoft Groups
- **SharePoint**: Backend storage, intranet/Teams integration, enterprise search
- **Intranet Portal**: SOP knowledge base, embedded widgets, navigation integration
- **HRMS**: Employee data sync, onboarding workflows, role-based access

## Wireframe Requirements

### User Roles (Based on SOP App Flow)

The system serves three main user roles:

1. **Process Champion** - Creates and edits SOPs
   - SSO Login (O365/AD)
   - Permission and folder management
   - SOP Creator/Editor with flowchart designer tool integration
   - Define users who can view each SOP
   - Submit SOPs for review
   - Receive and respond to feedback
   - Update SOPs based on review comments

2. **Process Owner/Sector Head** - Reviews and approves SOPs
   - Notification inbox for new SOP submissions
   - Review interface with feedback/remarks capability
   - Approval/rejection workflow
   - Multi-user review and approval support
   - Version auto-numbering interface
   - E-signature interface
   - Sign-off capability
   - Notify linked users when approved

3. **User (External/Internal)** - Views and accesses SOPs
   - Receive notifications for new/updated SOPs
   - Browse/searchable list of assigned SOPs
   - SOP document viewer
   - Access from any device (mobile, tablet, desktop)

### Key Interfaces to Design

1. **Process Champion Interfaces**
   - Login/SSO page
   - Permission and folder management dashboard
   - SOP Creator/Editor (with flowchart designer integration)
   - User definition/assignment interface
   - Submission interface
   - Feedback review and update interface

2. **Process Owner/Sector Head Interfaces**
   - Notification dashboard/inbox
   - Review and feedback interface
   - Approval workflow interface (single and multi-user)
   - Version management view
   - E-signature interface
   - Sign-off confirmation

3. **User (External/Internal) Interfaces**
   - Notification center
   - SOP Library/List view (searchable, filterable)
   - SOP Document viewer
   - Mobile-optimized views

### Design Principles
- User-centric, mobile-first, WCAG 2.1 AA compliant
- Consistent with Microsoft 365 design language
- Fast performance, clear visual indicators

### Key User Flows (Based on SOP App Flow)

**Process Champion Flow:**
1. **Create New SOP**: SSO Login → Set Permissions/Folders → Create/Edit SOP (with flowchart designer) → Define Users to View → Submit → Notify Process Owner
2. **Update SOP**: Receive Feedback → Update SOP → Create/Edit → Resubmit

**Process Owner/Sector Head Flow:**
1. **Review & Approve**: Receive Notification → Review SOP → Provide Feedback/Remarks → Approve? → (If No: Send back for Update) → (If Yes: Multi-user Approval?) → Auto-number Version → E-Signature → Sign Off → Notify Linked Users

**User (External/Internal) Flow:**
1. **Access SOP**: Receive Notification → See List of SOPs → View SOP Document

## Success Criteria
- Find SOPs within 3 clicks
- Clear version/compliance status visibility
- Streamlined workflows for policy owners
- Quick team compliance assessment for managers
- Full mobile functionality
- Seamless integration with digital workplace

## References
- Mockups: `/docs/Wireframe SOP.docx`, `/docs/Mockup SOP.docx`
- App Flow: `/docs/WhatsApp Image 2026-01-19 at 12.49.46.jpeg`
- Best Practices: [Xoralia Guide](https://xoralia.com/what-is-sop-management-software/)

---
**Version**: 1.0 | **Updated**: January 24, 2026 | **Status**: Draft
