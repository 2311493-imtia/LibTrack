# Software Requirements Specification (SRS) — LibTrack

| Field | Value |
|---|---|
| Product | LibTrack — Library Management System |
| Version | MVP + Beta |
| Releases | MVP — Mid-term, Beta — Final |
| Status | Draft |
| Related docs | [PRD](01-prd.md), [TDD](03-tdd.md) |

Every requirement is marked **MVP** (midterm) or **Beta** (final).

## Documents in this set
| Short form | Purpose | File |
|---|---|---|
| PRD | What we build and why | [01-prd.md](01-prd.md) |
| SRS | Requirements and acceptance criteria | [02-srs.md](02-srs.md) |
| TDD | Architecture, data model and API | [03-tdd.md](03-tdd.md) |

## 1. Introduction

### 1.1 Purpose
This document defines requirements for LibTrack, a library management system for book inventory, borrowing, returns, student history and overdue loans.

### 1.2 Scope
- **MVP:** book CRUD, search, basic borrowing/return records, persistent database, API documentation and deployment.
- **Beta:** login, Admin/Librarian/Student roles, account management, borrowing history, overdue tracking and security.
- Exclusions are listed in [PRD, section 5](01-prd.md#5-scope).

### 1.3 Definitions
| Term | Meaning |
|---|---|
| CRUD | Create, Read, Update, Delete |
| RBAC | Role-Based Access Control |
| Loan | A record linking a student and book, with borrow, due and return dates |
| Overdue | Due date has passed and the book has not been returned |
| Available copies | Copies currently available to borrow |

## 2. Overall description
LibTrack uses a React frontend, FastAPI backend and persistent PostgreSQL database. The browser does not connect directly to the database. During MVP, the API is a demonstration without role enforcement; Beta adds authentication and server-side permissions.

| User | Main responsibilities | Release |
|---|---|---|
| Demo user | Test book and loan API | MVP |
| Admin | Manage accounts, roles and account status | Beta |
| Librarian | Manage books, issue books and record returns | Beta |
| Student | Search catalogue and view own borrowing history | Beta |

## 3. Functional requirements

### 3.1 Books — MVP
| ID | Requirement | Priority | Release |
|---|---|---|---|
| FR-01 | Create a book with title, author, total copies and optional ISBN/year. | Must | MVP |
| FR-02 | List books with pagination. | Must | MVP |
| FR-03 | View one book's details and availability. | Must | MVP |
| FR-04 | Update an existing book. | Must | MVP |
| FR-05 | Delete a book only if it has no active loans. | Must | MVP |
| FR-06 | Search books by title or author. | Should | MVP |
| FR-07 | Validate required fields and inventory values. | Must | MVP |

### 3.2 Borrowing and returns — MVP
| ID | Requirement | Priority | Release |
|---|---|---|---|
| FR-08 | Create a loan with book, student identifier, borrow date and due date. | Must | MVP |
| FR-09 | Reject a loan when no copy is available. | Must | MVP |
| FR-10 | Record a return and restore availability exactly once. | Must | MVP |
| FR-11 | Reject a due date earlier than the borrow date. | Must | MVP |
| FR-12 | Prevent an already-returned loan from being returned again. | Must | MVP |

### 3.3 Authentication and accounts — Beta
| ID | Requirement | Priority | Release |
|---|---|---|---|
| FR-13 | Allow users to log in with valid credentials. | Must | Beta |
| FR-14 | Support logout and refresh-session revocation. | Must | Beta |
| FR-15 | Protect private API routes from unauthenticated requests. | Must | Beta |
| FR-16 | Allow users to view their profile and change password. | Should | Beta |
| FR-17 | Store passwords using a secure password hash. | Must | Beta |
| FR-18 | Limit repeated failed login attempts. | Must | Beta |

### 3.4 Roles and permissions — Beta
| ID | Requirement | Priority | Release |
|---|---|---|---|
| FR-19 | Support `admin`, `librarian` and `student` roles. | Must | Beta |
| FR-20 | Admins can create/deactivate accounts and assign roles. | Must | Beta |
| FR-21 | Librarians can add, edit and safely remove books. | Must | Beta |
| FR-22 | Librarians can issue books and record returns. | Must | Beta |
| FR-23 | Students can search and view book availability. | Must | Beta |
| FR-24 | Students can view only their own borrowing history. | Must | Beta |
| FR-25 | Students cannot manage inventory or mark their own loans returned. | Must | Beta |
| FR-26 | Enforce permissions in the backend, not only in the frontend. | Must | Beta |

### 3.5 Overdue tracking — Beta
| ID | Requirement | Priority | Release |
|---|---|---|---|
| FR-27 | Identify unreturned loans past their due date as overdue. | Must | Beta |
| FR-28 | Librarians can view active and overdue loans. | Must | Beta |
| FR-29 | Admins can view counts of books, users, active loans and overdue loans. | Should | Beta |
| FR-30 | Deactivated accounts cannot log in or use protected routes. | Must | Beta |
| FR-31 | Provide health endpoint and interactive API documentation at `/api/docs`. | Must | MVP |
| FR-32 | Return clear HTTP status codes and validation errors. | Must | MVP |
| FR-33 | Never expose password hashes, token hashes or secrets. | Must | Beta |

## 4. Non-functional requirements
| ID | Category | Requirement | Release |
|---|---|---|---|
| NFR-01 | Usability | Forms and actions have clear labels and feedback. | Beta |
| NFR-02 | Performance | Common catalogue requests should respond within 2 seconds under demo load. | MVP |
| NFR-03 | Reliability | Loan transactions keep availability and loan status consistent. | MVP |
| NFR-04 | Persistence | Data survives restarts and redeployments. | MVP |
| NFR-05 | Security | Protected routes enforce authentication and role authorization. | Beta |
| NFR-06 | Security | Passwords are hashed and secrets use environment variables. | Beta |
| NFR-07 | Maintainability | Code is separated into routers, schemas, services and models. | MVP |
| NFR-08 | Compatibility | Support recent major desktop browsers. | MVP |
| NFR-09 | Scalability | Book and loan lists support pagination. | MVP |
| NFR-10 | Error handling | Unexpected errors do not reveal internal details. | MVP |
| NFR-11 | Accessibility | Forms support keyboard use and readable error messages. | Beta |
| NFR-12 | Auditability | Borrow, due and return dates are preserved. | MVP |

## 5. Business rules
- **BR-01:** `total_copies` is an integer greater than or equal to zero.
- **BR-02:** `available_copies` must be between zero and `total_copies`.
- **BR-03:** Issuing a loan decreases availability by one; returning it increases availability by one.
- **BR-04:** Issuing and returning must use database transactions to prevent race conditions.
- **BR-05:** A loan must refer to an existing book and, in Beta, an active student account.
- **BR-06:** Due date cannot be earlier than borrow date.
- **BR-07:** A loan is overdue only if its due date is before today and `returned_at` is null.
- **BR-08:** A loan can be returned only once.
- **BR-09:** Books with active loans cannot be permanently deleted.
- **BR-10:** Admins manage accounts; librarians manage inventory and loans; students view the catalogue and their own history.

## 6. Permission matrix — Beta
| Action | Admin | Librarian | Student |
|---|---:|---:|---:|
| Search/view catalogue | Yes | Yes | Yes |
| Add/edit books | Yes | Yes | No |
| Delete book with no active loans | Yes | Yes | No |
| Issue books / record returns | No | Yes | No |
| View active/overdue loans | Overview | Yes | Own loans only |
| View own borrowing history | Support access | Operational access | Yes |
| Manage accounts and roles | Yes | No | No |
| View admin dashboard | Yes | No | No |

All authorization is checked by the API. Students must never access another student's history by changing a URL or request parameter.

## 7. Acceptance criteria

### MVP
- **AC-01:** Creating a valid book returns `201` and a saved ID.
- **AC-02:** Listing and searching books returns matching saved records and respects pagination.
- **AC-03:** Updating a missing book returns `404`; invalid fields return `422`.
- **AC-04:** A book with an active loan cannot be deleted.
- **AC-05:** Issuing an available copy creates a loan and decreases availability by one.
- **AC-06:** Issuing when no copy is available is rejected without changing data.
- **AC-07:** Returning a loan records the return and restores one copy exactly once.
- **AC-08:** `/api/health` succeeds and `/api/docs` loads.

### Beta
- **AC-09:** Missing or invalid credentials are rejected by protected endpoints.
- **AC-10:** Each role can perform only permitted actions.
- **AC-11:** Students cannot retrieve another student's borrowing history.
- **AC-12:** Deactivated accounts cannot log in.
- **AC-13:** Unreturned loans past due appear overdue; returned loans do not.
- **AC-14:** API responses never include password or refresh-token hashes.

## 8. Main use cases

### UC-01 — Search for a book
1. User opens the catalogue and enters a title or author keyword.
2. Frontend requests the book list endpoint.
3. API returns matching books and availability.
4. Frontend displays results or a no-results message.

### UC-02 — Issue a book (Beta)
1. Librarian selects a student, available book and due date.
2. API checks the librarian role, student status, due date and availability.
3. API creates the loan and decreases availability in one transaction.
4. Frontend shows the confirmed loan.

### UC-03 — Return a book (Beta)
1. Librarian opens an active loan and chooses Return.
2. API records the return date and restores availability once.
3. Frontend displays the completed return.

### UC-04 — View borrowing history (Beta)
1. Student signs in and opens Borrowing History.
2. API identifies the student from the authenticated session.
3. API returns only that student's current and past loans.

## 9. Traceability
| PRD feature | SRS requirements |
|---|---|
| Book CRUD/search | FR-01–FR-07 |
| Borrowing and returns | FR-08–FR-12 |
| Authentication | FR-13–FR-18 |
| Roles and account management | FR-19–FR-26 |
| Overdue tracking | FR-27–FR-30 |
| API docs, errors and security | FR-31–FR-33 |
| Data integrity | BR-01–BR-10, NFR-03–NFR-06 |
