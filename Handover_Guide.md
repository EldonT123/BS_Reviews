# Banana Slugs Movie Review System - Deployment and Handover Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation Instructions](#installation-instructions)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Initial Setup](#initial-setup)
7. [Maintenance Requirements](#maintenance-requirements)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

The Banana Slugs Movie Review System is a full-stack web application consisting of:
- **Backend**: FastAPI (Python) REST API
- **Frontend**: Next.js (React/TypeScript)
- **Database**: CSV-based file storage
- **Deployment**: Docker containers

---

## Prerequisites

### Required Software
- **Docker**: Version 20.10 or higher
- **VScode**: Latest verision ideally.
- **Docker Compose**: Version 2.0 or higher (optional, for multi-container setup)
- **Git**: For cloning the repository

### System Requirements
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB free space
- **Ports**: 8000 (backend), 3000 (frontend)

---

## Installation Instructions

### Step 1: Clone the Repository
Ensure that you clone the repository in a folder that makes sense for your testing purposes. Aditionally, the usage of VS codes clone repository feature can also make this process easier.
```bash
git clone <https://github.com/EldonT123/Banana_Slugs.git>
cd Banana_Slugs
```

### Step 2: Verify Project Structure

Ensure the following directory structure exists:

```
Banana_Slugs/
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── middleware/
├── frontend/bs_reviews
│   ├── app/
│   ├── public/
│   └── package.json
├── database/
│   └── archive/
├── .docker/
│   ├── backend.dockerfile
│   └── frontend.dockerfile
└── README.md
```
In adition to this you'll also see our test folders which have the tests organized in the same folder structure as the actual project, but then each folder is broken down into primary services or routes which each have a sub folder containing either unit tests or intergration tests.
### Step 3: Build Docker Images

#### Backend Image
To be done in the root directory of the project.
```bash
docker build -f .docker/backend.dockerfile -t banana-slugs-backend .
```

#### Frontend Image (if applicable)
To be done in the root directory of the project.
```bash
docker build -f .docker/frontend.dockerfile -t banana-slugs-frontend .
```

**Build Time**: Expect about 20 seconds for the backend image and 2-3 minutes for the frontend container.

---

## Configuration

### Backend Configuration

#### Database Setup
The database uses CSV files stored in `database` folder. The system automatically creates necessary files on the first run. Some test data exists in the user based CSV files as well as the admin based CSV files as well. 

**Initial Database Structure**:
```
database/
|----- admins/
|       |-- admin_information.csv
|
|----- users/
|       |- purchase_history.csv
|       |- user_bookmarks.csv
|       |- user_infromation.csv
|       └── banned_emails.csv
|       
└── archive/
    └── [Movie Name]/
        ├── metadata.json
        ├── movieReviews.csv
        └── streamingData.csv
```

## Running the Application

### Option 1: Using Docker (Recommended)

#### Start Backend
```bash
docker run -p 8000:8000 banana-slugs-backend
```

#### Start Frontend (in a separate terminal)
```bash
docker run -p 3000:3000 banana-slugs-frontend
```

#### Using Docker Compose (if configured)
```bash
docker-compose up -d
```

### Option 2: Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
fastapi run main.py
```

#### Frontend
```bash
cd frontend/bs_reviews
npm install
npm run dev
```

### Verify Installation

1. **Backend API**: Navigate to `http://localhost:8000/docs`
   - You should see the FastAPI Swagger documentation
   
2. **Frontend**: Navigate to `http://localhost:3000`
   - You should see the home page

---

## Initial Setup

---

## Part A: User Setup and Testing

### Step 1: User Signup Process

1. Navigate to `http://localhost:3000`
2. Click the **"Login"** or **"Sign Up"** button in the top navigation
3. On the login page, click **"Sign Up"** at the bottom
4. Fill out the signup form with the following requirements:
   - **Email**: Valid email format (e.g., `user@test.com`)
   - **Username**: Minimum 3 characters (e.g., `test_user`)
   - **Password**: Must meet all requirements:
     - At least 8 characters
     - Contains uppercase letter
     - Contains lowercase letter
     - Contains a number
     - Contains a special character (e.g., `TestUser123!`)
   - **Confirm Password**: Must match the password field
5. Click **"Sign Up"**
6. You should see a success message: "Signup successful! Please log in."

**Example Test User**:
```
Email: testuser@example.com
Username: testuser
Password: TestUser123!
```

**Note**: New users start as **Snail Tier** by default (view-only access).

### Step 2: User Login Process

1. After signup, you'll be redirected to the login page
2. Enter your credentials:
   - **Email**: The email you used during signup
   - **Password**: Your password
3. Click **"Sign In"**
4. Upon successful login, you'll be redirected to the home page
5. You should now see **Account** in the top navigation bar

**Verification**:
- Your session is now active (stored in localStorage)
- You can access user-specific features

### Step 3: Exploring the Store (Tier Upgrades)

1. From the home page, click **"Store"** in the navigation menu
2. You'll see three tier options:

#### Tier Overview:
- **🐌 Snail Tier (Free)**:
  - View movies and reviews
  - Cannot write reviews
  
- **🐌 Slug Tier ($5.00 or 500 tokens)**:
  - Everything in Snail tier
  - Write and edit reviews
  - Like/dislike other reviews
  - Rate movies
  
- **🍌 Banana Slug Tier ($10.00 or 1000 tokens)**:
  - Everything in Slug tier
  - Priority review placement (your reviews appear first)
  - Premium badge on reviews

3. To upgrade, click **"Purchase"** on your desired tier

### Step 4: Payment Process

The system supports two payment methods:

#### Option A: Token Payment (In-App Currency)
1. Click **"Purchase"** on a tier card
2. If you have sufficient tokens, you'll see a confirmation dialog
3. Click **"Confirm Purchase"**
4. Your tier will be upgraded immediately
5. Tokens will be deducted from your account balance

**Note**: Default users start with 0 tokens. Tokens can be:
- Earned through platform activities (Not fully Implemented intime for use)
- Purchased with real money
- Granted by administrators

#### Option B: Cash Payment (Credit-card)
1. Click **"Purchase"** on a tier card
2. If you don't have enough tokens, you'll see the cash price option
3. Click **"Pay with Card"** (doesn't actually charge a card)
4. Enter payment details:
   - Card number: `4242 4242 4242 4242` (test card)
   - Expiry: Any future date (e.g., `12/25`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)
5. Click **"Pay"**
6. Upon successful payment:
   - Your tier is upgraded
   - You receive a confirmation message

### Step 5: Searching for Movies

1. On the home page, use the **search bar** at the top
2. Type a movie name (e.g., "Spider-Man", "Avengers", "Joker")
3. The search is real-time and filters as you type

#### Filter Process:
1. Click the **"Filter"** button next to the search bar
2. Available filters:
   - **Genre**: Action, Drama, Comedy, Horror, etc.
   - **Year**: Release year range
   - **Rating**: Minimum IMDb rating
   
3. Select your desired filters
4. Click **"Apply Filters"**
5. The movie grid will update to show only matching movies

#### Filter Examples:
- **Action movies from 2020+**:
  - Genre: Action
  - Year: 2020-2024
  
- **Highly rated comedies**:
  - Genre: Comedy
  - Rating: 7.5+

### Step 6: Writing and Interacting with Reviews

#### Prerequisites:
- You must be **Slug Tier or higher** to write reviews
- If you're Snail Tier, upgrade first (see Step 3)

#### Writing a Review:
1. Click on any movie card to open the movie details page
2. Scroll down to the **"Write a Review"** section
3. Fill out the review form:
   - **Rating**: Select 0-10 stars
   - **Review Title**: Brief headline (e.g., "Amazing Movie!")
   - **Review Text**: Your detailed thoughts (optional)
4. Click **"Submit Review"**
5. Your review will appear in the reviews section immediately

**Review Features**:
- **Edit**: Click the edit icon on your own reviews to modify them
- **One review per movie**: You can only have one review per movie

#### Liking and Disliking Reviews:
1. Scroll through the reviews on a movie page
2. Each review has **👍 Like** and **👎 Dislike** buttons
3. Click **Like** to agree with a review (like count increases)
4. Click **Dislike** if you disagree (dislike count increases)

#### Reporting Reviews:
1. Scroll through the reviews on a movie page
2. Each review has a **Report** button
3. Click **Report** to report a review
4. Add your report reason, a report will be sent to the administrators (see admin section)

**Rules**:
- You can only vote once per review
- Clicking **Like** removes any previous **Dislike** (and vice versa)
- You cannot like/dislike your own reviews
- Your account must not be banned from reviewing

#### Review Display Order:
- **Banana Slug Tier** reviews appear **first** (priority placement, not fully implemented)
- Regular **Slug Tier** reviews appear after

### Step 7: Account Page

1. Click your **Account** in the top navigation bar
2. The account page displays:

#### User Information:
- **Email**: Your registered email address
- **Username**: Your display name
- **Tier**: Current tier level with icon (🐌 Snail, 🐌 Slug, or 🍌 Banana Slug)
- **Tokens**: Current token balance
- **Account Status**: Shows if you have been banned from reviewing 

#### Review History:
- List of all your submitted reviews
- Shows:
  - Movie name
  - Your rating
  - Review title
  - Date posted
  - Like/dislike counts
- Click any review to view the full movie page

### Step 8: Account Settings

1. From the account page, click **"Settings"** or the gear icon
2. Available settings:

#### Change Username:
1. Click **"Edit Username"**
2. Enter new username (minimum 3 characters)
3. Click **"Save"**

#### Change Email:
1. Click **"Edit Email"**
2. Enter new email address
3. Verify current password for security
4. Click **"Save"**
5. You'll be logged out and need to log in with the new email

#### Change Password:
1. Click **"Change Password"**
2. Enter:
   - **Current Password**: For verification
   - **New Password**: Must meet password requirements
   - **Confirm New Password**: Must match
3. Click **"Update Password"**
4. You'll be logged out and need to log in with the new password

#### Download User Information:
1. Click **"Download My Data"**
2. A JSON file will be downloaded containing:
   - Account information (email, username, tier)
   - All your reviews
   - Token balance

**File Format** (`user_data_[email].json`):
```json
{
  "email": "user@example.com",
  "username": "testuser",
  "tier": "slug",
  "tokens": 150,
  "created_at": "2024-01-15",
  "reviews": [
    {
      "movie": "Test Movie",
      "rating": 8.5,
      "title": "Great film",
      "comment": "Really enjoyed it",
      "date": "2024-02-20"
    }
  ]
}
```

## Part B: Admin Setup and Management

### Step 9: Create Admin Account

Admins can only be created by other admins or by using the Swagger FastAPI endpoints

#### Option A: Sign up using endpoints

1. Navigate to `http://localhost:8000/docs`
2. Click the **"Sign Up"** endpoint
3. Fill out the admin signup form:
   - **Email**: Use a dedicated admin email
   - **Password**: Strong password meeting all requirements
4. Click **"Execute"**

**Note**: Admin accounts are separate from user accounts and stored in a different database file. An admin can have a separate user account on the same email.

#### Option B: Sign up using admin dashboard

1. Log into admin dashboard (See step 10)
2. Navigate to **"Users"** page on left
3. Press make admin on any existing user.
4. Enter your admin password to authenticate. This will make a new admin account with the same credentials as the existing user.
5. Log in with new admin account (See step 10)

### Step 10: Admin Login and Dashboard Access

1. Log in using your admin credentials at `/admin/login`
2. Upon successful login, you'll access the **Admin Dashboard**
3. Dashboard sections:
   - **Dashboard**: View platform metrics
   - **Users**: View, upgrade, delete users
   - **Penalities**: Apply penalties to users, review ban, token removal, complete ban
   - **Movies**: Add, edit, delete movies
   - **Reviews**: Handle reported reviews

### Step 11: User Management (Admin)

#### View All Users:
1. Navigate to **Admin Dashboard** → **User Management**
2. You'll see a table of all registered users showing:
   - Email
   - Username
   - Current tier

#### Manually Upgrade User Tiers:
1. Find the user in the user list
2. Click **"Edit"** or the tier dropdown next to their name
3. Select new tier:
   - Snail Tier (view only)
   - Slug Tier (can review)
   - Banana Slug Tier (priority reviews)
4. Click **"Update Tier"**
5. User will see updated permissions immediately

**Example**: Upgrading test accounts:
- `snail@test.com` → Keep as Snail tier
- `slug@test.com` → Upgrade to Slug tier
- `banana@test.com` → Upgrade to Banana Slug tier

### Step 12: Penlty Management (Admin)

#### Remove Tokens to Users:
1. Click **"Remove Tokens"** next to a user
2. Enter token amount to remove (e.g., 500)
3. Click **"Remove Tokens"**

#### Ban/Unban Users:
1. Click **"Ban User"** next to a problematic user
2. Enter ban reason (e.g., "Spam reviews", "Inappropriate content")
3. Confirm ban
4. Banned users:
   - Cannot log in
   - All reviews are hidden
   - Email is blacklisted from new signups
5. To unban: Click **"Unban"** and confirm

#### Review Ban (Without Account Ban):
1. Click **"Review Ban"** for users who violate review policies
2. User can still log in and browse
3. User **cannot** write, edit, or interact with reviews
4. Existing reviews are marked as penalized and hidden
5. To unban from reviews: Click **"Unban from Reviews"**

### Step 13: Movie Management (Admin)

#### Add New Movies:
1. Navigate to **Admin Dashboard** → **Movie Management**
2. Click **"Add Movie"**
3. Fill out the movie form:

**Required Fields**:
- **Movie Name(Folder)**: `test_movie` (used for folder name, no special characters)
- **Title**: `Test Movie` (shown to users)

**Optional Fields**:
- **Description**: Movie plot summary
- **Duration**: Runtime in minutes
- **Cast**: Main actors
- **Total Rating Count**: Number of IMDb ratings
- **Metascore**: Metacritic score
- **Director**: `Test Director`
- **Genre**: Select from dropdown or enter (e.g., `Action, Drama`)
- **Release Year**: `2024`
- **IMDb Rating**: `7.5` (0-10 scale)

**Important**: Movie names with special characters are automatically sanitized:
- "Spider-Man: No Way Home" → stored as "SpiderMan No Way Home"
- Use sanitized name for folder operations

#### Edit Existing Movies:
1. Find the movie in the movie list
2. Click **"Edit"** next to the movie
3. Modify any fields
4. Click **"Save Changes"**
5. Changes reflect immediately on the site

#### Delete Movies:
1. Find the movie in the movie list
2. Click **"Delete"** (red button)
3. Confirm deletion in the warning popup
4. **Warning**: This permanently deletes:
   - Movie metadata
   - All user reviews for that movie
   - Poster image
   - Movie folder and all contents

### Step 13: Review Moderation (Admin)

#### View Reported Reviews:
1. Navigate to **Admin Dashboard** → **Review Moderation**
2. You'll see all reviews that have been reported by users
3. Each report shows:
   - Review content
   - Author information
   - Report reasons
   - Number of reports
   - Review status (visible/hidden)

#### Handle Reported Reviews:
1. Click on a reported review to expand details
2. Read the review and report reasons
3. Choose an action:

**Option A: Keep Review (False Report)**
- Click **"Keep Review"**
- Report flags are cleared
- Review becomes visible again
- Reporter is not notified

**Option B: Remove Review (Violates Policy)**
- First, **"Penalize User"** using penalize page
- Then click **"Delete Review"**
- Review is permanently removed
- User receives a warning
- Can lead to review ban if repeated

---

## Maintenance Requirements

### Account Management

#### Admin Accounts
- **Location**: `database/admins/admin_information.csv`
- **Credentials**: Store admin passwords in a secure password manager

#### User Management
- **Locations**: 
   - `database/users/user_information.csv`
   - `database/admins/banned_emails.csv`
   - `database/users/purchase_history.csv`
   - `database/users/user_bookmarks.csv`
- **Tasks**:
  - Monitor user signups
  - Upgrade user tiers as needed
  - Ban problematic users via admin panel
  - Save user purchases and bookmarks

### Database Management

#### Database Maintenance Tasks

1. **Monthly**: Review and clean up old reviews
2. **Quarterly**: Archive inactive user accounts
3. **Yearly**: Database optimization and cleanup

#### CSV File Structure

**user_information.csv**:
```csv
user_email,user_password,user_tier,tokens,review_banned
user@example.com,hashed_password,slug,0,False
```

**movieReviews.csv** (per movie):
```csv
Date of Review,Email,Username,Dislikes,Likes,User's Rating out of 10,Review Title,Review,Reported,Report Reason,Report Count,Penalized,Hidden,Liked By,Disliked By
2024-01-01,user@test.com,testuser,0,5,8.5,Great Movie,Loved it!,No,,0,No,No,,
```

### Monitoring and Logs

#### View Docker Logs
```bash
# Backend logs
docker logs -f <backend-container-id>

# Frontend logs  
docker logs -f <frontend-container-id>
```

#### Important Log Files
- Backend errors: Check Docker logs
- Database operations: Console output during runtime
- Failed logins: Check `backend/logs/` (if implemented)

#### Dependency Updates

**Backend (Python)**:
```bash
# Check for updates
pip list --outdated

# Update dependencies
pip install --upgrade -r requirements.txt
```

**Frontend (Node.js)**:
```bash
# Check for updates
npm outdated

# Update dependencies
npm update

# Security audit
npm audit fix
```


---

## Troubleshooting

### Common Issues


#### Issue: Docker Build Fails
```bash
# Solution: Clear Docker cache
docker system prune -a
docker build --no-cache -f .docker/backend.dockerfile -t banana-slugs-backend .
```

#### Issue: Database Not Found
```bash
# Solution: Ensure database directory exists
mkdir -p database/archive

# Create empty CSV files
touch database/user_information.csv
touch database/admin_information.csv
touch database/banned_emails.csv
```

#### Issue: Reviews Not Showing
**Cause**: Movie folder name mismatch (special characters)

**Solution**: Movie names with special characters are sanitized:
- "Spider-Man: No Way Home" → "SpiderMan No Way Home"
- Use the sanitized name when accessing reviews

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure production database backups
- [ ] Set up monitoring and alerting
- [ ] Update CORS origins for production domain
- [ ] Configure external API keys
- [ ] Test all user flows
- [ ] Set up automated backups
- [ ] Document custom configurations
- [ ] Create admin accounts for team members
- [ ] Test disaster recovery procedures


---

## Version History

- **v1.0.0** (2024-12-04): Initial deployment guide
- Document updated by: [Your team name]
- Last reviewed: December 4, 2024

---

*This guide should be updated whenever significant changes are made to the deployment process or system architecture.*