# DevOps Blog

A simple personal blog built with **Flask**, **Bootstrap 5**, and **SQLAlchemy**. This project serves as both a learning experience and a platform to share ideas, articles, and more.

## Features

- **User Authentication**: Allows users to register, log in, and log out.
- **Create, Edit, and Delete Posts**: Only authenticated users (admin) can manage blog posts.
- **Comment Section**: Users can leave comments on blog posts (requires authentication).
- **Email Contact Form**: Users can contact the owner via an email form.
- **Responsive Design**: Built with **Bootstrap 5**, ensuring a responsive layout for both desktop and mobile users.

## Technologies Used

- **Flask**: Python web framework.
- **Flask-SQLAlchemy**: ORM for interacting with the database.
- **Flask-Login**: User session management.
- **Flask-Mail**: Sending emails via Gmail.
- **Flask-WTF**: Forms handling with validation.
- **Flask-CKEditor**: Rich text editing for comments and blog content.
- **Bootstrap 5**: Frontend framework for responsive design.

## Usage

- **Homepage**: Displays a list of blog posts.
- **Login**: Access the login page for authentication.
- **New Post**: If you're an admin, you can create and manage blog posts.
- **Comments**: Users can comment on individual blog posts (authenticated users only).
- **Contact Form**: Send messages to the blog owner via the contact form.
