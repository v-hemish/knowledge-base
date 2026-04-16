Here’s a clean full problem statement you can work from:

## Problem Statement

Design and implement the backend for a **movie seat reservation system** using **FastAPI**, where users can view showtimes, check seat availability, temporarily lock seats for a short period, and confirm bookings before the lock expires. The system must ensure that a seat cannot be booked by more than one user for the same showtime.

The backend should model the real-world challenge of ticket booking systems where multiple users may try to reserve the same seat at nearly the same time. To handle this, the system should support a **time-bound seat locking mechanism**. When a user selects a seat, that seat should be marked as temporarily unavailable to others for a fixed duration. If the user confirms the booking before the lock expires, the seat becomes permanently booked. If the user does not confirm in time, the lock should expire and the seat should become available again.

The system should maintain accurate seat availability for every showtime by classifying each seat as **available**, **locked**, or **booked**. A booked seat must always remain unavailable. A locked seat must remain unavailable only until its lock expires. Expired locks should not continue blocking the seat.

The backend should expose APIs to:

* create and list movies
* create and list showtimes for movies
* view seat availability for a given showtime
* place a temporary lock on a seat
* confirm a booking using a valid active lock

The implementation should focus on **backend design, data modeling, validation, state transitions, and business logic**, rather than UI, authentication, or payment integration.

## Functional Requirements

The system must:

* allow creation of movies
* allow creation of showtimes for a movie
* store the total number of seats for each showtime
* allow a user to request a temporary lock on a seat for a given showtime
* reject a lock request if the seat is already booked
* reject a lock request if the seat is already actively locked by another user
* allow a user to confirm a booking only if they hold a valid, unexpired lock for that seat
* mark the seat as booked after successful confirmation
* treat expired locks as inactive and make those seats available again
* return current seat availability for a showtime

## Non-Functional Focus

This project should specifically help practice:

* REST API design with FastAPI
* relational data modeling
* business-rule validation
* time-based state handling
* preventing double-booking
* clean service-layer backend logic

## Constraints for Today’s Version

To keep the project focused and achievable in a few hours, the implementation should **not** include:

* user authentication
* payments
* theater or screen hierarchy
* seat categories like VIP or regular
* notifications
* background schedulers
* admin dashboards

A simple `user_name` or `client_id` string is enough to represent the user making the lock or booking.

## Core Real-World Problem Being Solved

The main backend challenge is:

> How can the system prevent two users from reserving the same seat for the same showtime while still allowing one user to temporarily hold a seat before final confirmation?

## Success Criteria

The project is successful if:

* a movie can be created
* a showtime can be created for that movie
* seat availability can be viewed for that showtime
* one user can lock a seat
* another user cannot lock the same seat while that lock is active
* the first user can confirm the booking before expiry
* the seat then appears as booked
* expired locks no longer block seat availability

## One-Line Version

Build a FastAPI backend for a movie booking system that uses temporary seat locks and booking confirmation to prevent double-booking for the same showtime.

If you want, I’ll turn this into a more interview/case-study style project brief you can paste at the top of your README.

