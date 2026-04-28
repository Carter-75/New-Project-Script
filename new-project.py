#!/usr/bin/env python3
import os
import json
import subprocess
import ctypes
from pathlib import Path

def ask_input(prompt, default=None, validation_func=None, options=None):
    """
    Robust input loop that handles defaults and validation.
    Displays 'oops wrong input' on failure.
    """
    first_attempt = True
    while True:
        if not first_attempt:
            print("oops wrong input")
        
        display_prompt = f"{prompt}"
        if options:
            display_prompt += f" ({'/'.join(options)})"
        if default:
            display_prompt += f" [default: {default}]"
        
        user_input = input(f"{display_prompt}: ").strip()
        
        # Handle default
        if user_input == "" and default is not None:
            return default
            
        # Validation
        if not user_input and default is None:
            first_attempt = False
            continue
            
        if options and user_input not in options:
            first_attempt = False
            continue
            
        if validation_func and not validation_func(user_input):
            first_attempt = False
            continue
            
        return user_input

def main():
    # 0. Safety Check for Admin (Windows)
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() != 0:
            print("--- WARNING: SCRIPT RUNNING AS ADMINISTRATOR ---")
            print("Creating projects as Admin can make them hard to delete later.")
            print("It is recommended to run this in a standard user terminal.\n")
    except AttributeError:
        # Non-Windows systems ignore this
        pass

    print("--- Unified MEAN Project Generator (Angular + Express + Mongo) ---")
    print("      Features: Physics (Matter.js), Anime.js, Iframe Security\n")

    # 1. Gather Inputs
    project_name = ask_input(
        "Project Name", 
        validation_func=lambda x: (
            len(x) <= 100 and 
            x.islower() and 
            all(c.isalnum() or c in '._-' for c in x) and 
            '---' not in x
        )
    )
    project_slug = project_name.lower()
    
    fe_port = ask_input(
        "Frontend Port", 
        default="4200", 
        validation_func=lambda x: x.isdigit()
    )
    
    be_port = ask_input(
        "Backend Port", 
        default="3000", 
        validation_func=lambda x: x.isdigit()
    )
    
    css_choice = ask_input(
        "CSS Flavor / Framework", 
        default="tailwind", 
        options=["css", "scss", "bulma", "tailwind"]
    )
    
    use_matter = ask_input(
        "Do you want Matter.js?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    use_anime = ask_input(
        "Do you want Anime.js?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    use_confetti = ask_input(
        "Do you want Confetti?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    use_gsap = ask_input(
        "Do you want GSAP (Animations)?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    use_three = ask_input(
        "Do you want Three.js (3D)?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    use_lenis = ask_input(
        "Do you want Lenis (Smooth Scroll)?", 
        default="yes", 
        options=["yes", "no"]
    ) == "yes"

    ai_choice = ask_input(
        "Which AI tools do you want to configure?", 
        default="Agents.md", 
        options=["Agents.md", "Cursor", "Claude", "None"]
    )

    auth_choice = ask_input(
        "Authentication Type",
        default="None",
        options=["None", "Local", "Google", "Both"]
    )

    fe_hosting = ask_input(
        "Frontend Hosting",
        default="vercel",
        options=["vercel", "other"]
    )

    be_hosting = ask_input(
        "Backend Hosting",
        default="vercel",
        options=["vercel", "other"]
    )
    
    project_root = Path.cwd() / project_name
    if project_root.exists():
        print(f"Error: Directory {project_name} already exists.")
        return

    project_root.mkdir()
    backend_root = project_root / "backend"
    frontend_root = project_root / "frontend"
    backend_root.mkdir()
    frontend_root.mkdir()

    print(f"\nCreating project '{project_name}' in {project_root}...")

    # --- Backend Templates ---
    be_dependencies = {
        "express": "^4.19.2",
        "cors": "^2.8.5",
        "cookie-parser": "~1.4.6",
        "debug": "~2.6.9",
        "morgan": "~1.10.0",
        "mongoose": "^8.0.0",
        "helmet": "^7.1.0",
        "dotenv": "^16.4.5",
        "openai": "^4.55.0",
        "ws": "^8.18.0",
        "zod": "^3.23.8"
    }

    if auth_choice != "None":
        be_dependencies.update({
            "express-session": "^1.18.0",
            "passport": "^0.7.0",
            "bcryptjs": "^2.4.3"
        })
    
    if auth_choice in ["Google", "Both"]:
        be_dependencies.update({
            "passport-google-oauth20": "^2.0.0"
        })

    be_package_json = {
        "name": f"{project_name}-backend",
        "version": "1.0.0",
        "scripts": {
            "start": "node ./bin/www",
            "dev": "nodemon ./bin/www"
        },
        "dependencies": be_dependencies,
        "devDependencies": {
            "nodemon": "^3.1.0"
        }
    }

    # --- Backend Template Logic ---
    session_require = "const session = require('express-session');" if auth_choice != "None" else ""
    passport_require = "const passport = require('passport');" if auth_choice != "None" else ""
    passport_config_require = "require('./config/passport')(passport);" if auth_choice != "None" else ""
    auth_router_require = "const authRouter = require('./routes/auth');" if auth_choice != "None" else ""
    
    session_init = ""
    if auth_choice != "None":
        session_init = f"""// Sessions
app.use(
  session({{
    secret: process.env.SESSION_SECRET || 'secret',
    resave: false,
    saveUninitialized: false,
    cookie: {{
      secure: isProd,
      sameSite: isProd ? 'none' : 'lax'
    }}
  }})
);

// Passport
app.use(passport.initialize());
app.use(passport.session());"""

    auth_mounts = ""
    if auth_choice != "None":
        auth_mounts = "app.use('/api/auth', authRouter);\napp.use('/auth', authRouter);"

    be_app_js = f"""// --- Environment and Dependencies ---
const path = require('path');
const fs = require('fs');
const dns = require('node:dns');
dns.setServers(['8.8.8.8', '1.1.1.1']);

const resolveEnvPath = () => {{
  const candidates = [
    path.join(process.cwd(), '.env.local'), 
    path.join(process.cwd(), 'backend', '.env.local'),
    path.join(__dirname, '../.env.local')
  ];
  for (const c of candidates) {{ if (fs.existsSync(c)) return c; }}
  return null;
}};
const envPath = resolveEnvPath();
if (envPath) require('dotenv').config({{ path: envPath }});
else require('dotenv').config();

const express = require('express');
const cookieParser = require('cookie-parser');
const logger = require('morgan');
const cors = require('cors');
const mongoose = require('mongoose');
const helmet = require('helmet');
{session_require}
{passport_require}

const app = express();

// --- Configuration ---
const isProd = process.env.PRODUCTION === 'true' || process.env.VERCEL === '1';
const prodUrl = process.env.PROD_FRONTEND_URL;
const PROJECT_NAME = process.env.PROJECT_NAME || '{project_name}';

// Trust proxy for secure cookies on Vercel
if (isProd) {{
  app.set('trust proxy', 1);
}}

// --- Models & Passport Config ---
{passport_config_require}

// --- Routers ---
const indexRouter = require('./routes/index');
{auth_router_require}

// --- Diagnostic Routes ---
app.get('/api/health', async (req, res) => {{
  const isConnected = mongoose.connection.readyState === 1;
  res.json({{
    status: 'online',
    database: isConnected ? 'Connected' : 'Disconnected',
    env: isProd ? 'production' : 'development',
    timestamp: new Date().toISOString()
  }});
}});

// --- MongoDB Setup ---
const mongoURI = process.env.MONGODB_URI;

const connectDB = async () => {{
  if (mongoose.connection.readyState >= 1) return;
  
  if (!mongoURI) {{
    console.warn('WARN: No MONGODB_URI found in environment!');
    return;
  }}

  try {{
    console.log('INFO: Connecting to MongoDB...');
    await mongoose.connect(mongoURI, {{
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 10000
    }});
    console.log('OK: Connected to MongoDB');
  }} catch (err) {{
    console.error('ERROR: MongoDB Connection Failed:', err.message);
  }}
}};

// Initial connection
connectDB();

// --- Middlewares ---

// Wait for DB middleware
const dbCheck = async (req, res, next) => {{
  if (mongoose.connection.readyState === 1) return next();
  if (mongoose.connection.readyState === 0) await connectDB();
  
  let attempts = 0;
  const interval = setInterval(() => {{
    attempts++;
    if (mongoose.connection.readyState === 1) {{
      clearInterval(interval);
      return next();
    }}
    if (attempts >= 30) {{
      clearInterval(interval);
      return res.status(503).json({{ 
        error: 'Database connection timeout. Please refresh or check MONGODB_URI.' 
      }});
    }}
  }}, 100);
}};

app.use(helmet({{
  frameguard: false,
  contentSecurityPolicy: false
}}));

app.use(cors({{
  origin: true,
  credentials: true
}}));

// Apply DB check to all /api routes
app.use('/api', dbCheck);

app.use(cors({{
  origin: true,
  credentials: true
}}));

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({{ extended: false }}));
app.use(cookieParser());

{session_init}

app.get('/', (req, res) => {{
  res.send(`API for ${{PROJECT_NAME}} is running`);
}});

// Mount at both /api and root to handle Vercel Service prefix stripping
app.use('/api', indexRouter);
app.use('/', indexRouter);

{auth_mounts}

// Error handler
app.use((err, req, res, next) => {{
  res.status(err.status || 500).json({{
    message: err.message,
    error: isProd ? {{}} : err
  }});
}});

module.exports = app;
"""



    be_www = """#!/usr/bin/env node
require('dotenv').config({ path: require('path').join(__dirname, '../../.env.local') });
const app = require('../app');
const http = require('http');

const port = process.env.PORT || '3000';
app.set('port', port);

const server = http.createServer(app);
server.listen(port, () => {
  console.log(`Backend listening on port ${port} (Project: ${process.env.PROJECT_NAME})`);
});
"""

    be_routes_index = """const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ message: 'Welcome to the API' });
});

module.exports = router;
"""

    google_strategy_import = "const GoogleStrategy = require('passport-google-oauth20').Strategy;" if auth_choice in ["Google", "Both"] else ""
    
    google_strategy_config = ""
    if auth_choice in ["Google", "Both"]:
        google_strategy_config = f"""// Google Strategy
  passport.use(
    new GoogleStrategy(
      {{
        clientID: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL: '/auth/google/callback',
        proxy: true
      }},
      async (accessToken, refreshToken, profile, done) => {{
        try {{
          let user = await User.findOne({{ googleId: profile.id }});
          if (!user) user = await User.findOne({{ email: profile.emails[0].value }});
          
          if (!user) {{
            user = await User.create({{
              googleId: profile.id,
              email: profile.emails[0].value,
              displayName: profile.displayName,
              firstName: profile.name.givenName,
              lastName: profile.name.familyName
            }});
          }} else if (!user.googleId) {{
            user.googleId = profile.id;
            await user.save();
          }}
          return done(null, user);
        }} catch (err) {{
          return done(err);
        }}
      }}
    )
  );"""

    be_passport_js = f"""const LocalStrategy = require('passport-local').Strategy;
{google_strategy_import}
const User = require('../models/user');

module.exports = function(passport) {{
  passport.serializeUser((user, done) => done(null, user.id));
  passport.deserializeUser(async (id, done) => {{
    try {{
      const user = await User.findById(id);
      done(null, user);
    }} catch (err) {{
      done(err);
    }}
  }});

  // Local Strategy
  passport.use(
    new LocalStrategy({{ usernameField: 'email' }}, async (email, password, done) => {{
      try {{
        const user = await User.findOne({{ email: email.toLowerCase() }});
        if (!user) return done(null, false, {{ message: 'Incorrect email or password.' }});

        const isMatch = await user.comparePassword(password);
        if (!isMatch) return done(null, false, {{ message: 'Incorrect email or password.' }});

        return done(null, user);
      }} catch (err) {{
        return done(err);
      }}
    }})
  );

  {google_strategy_config}
}};
"""

    be_user_model = """const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true, lowercase: true },
  password: { type: String, required: function() { return !this.googleId; } },
  googleId: { type: String },
  firstName: { type: String, required: true },
  lastName: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

userSchema.pre('save', async function(next) {
  if (!this.isModified('password') || !this.password) return next();
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

userSchema.methods.comparePassword = async function(candidatePassword) {
  if (!this.password) return false;
  return await bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', userSchema);
"""

    google_auth_routes = ""
    if auth_choice in ["Google", "Both"]:
        google_auth_routes = f"""
router.get('/google', passport.authenticate('google', {{ scope: ['profile', 'email'] }}));

router.get('/google/callback', (req, res, next) => {{
  passport.authenticate('google', (err, user, info) => {{
    if (err || !user) {{
      const frontendUrl = process.env.PROD_FRONTEND_URL || 'http://localhost:{fe_port}';
      return res.redirect(`${{frontendUrl}}/login?error=google`);
    }}
    
    req.login(user, (err) => {{
      if (err) return next(err);
      const frontendUrl = process.env.PROD_FRONTEND_URL || 'http://localhost:{fe_port}';
      res.redirect(`${{frontendUrl}}/dashboard`);
    }});
  }})(req, res, next);
}});
"""

    be_auth_routes = f"""const express = require('express');
const passport = require('passport');
const router = express.Router();
const User = require('../models/user');
const bcrypt = require('bcryptjs');

// --- Local Auth ---
router.post('/register', async (req, res) => {{
  try {{
    const {{ email, password, firstName, lastName }} = req.body;
    let user = await User.findOne({{ email: email.toLowerCase() }});
    if (user) return res.status(400).json({{ message: 'User already exists' }});

    user = await User.create({{ 
      email: email.toLowerCase(), 
      password, 
      firstName, 
      lastName 
    }});
    
    req.login(user, (err) => {{
      if (err) return res.status(500).json({{ error: err.message }});
      res.status(201).json(user);
    }});
  }} catch (err) {{
    res.status(500).json({{ error: err.message }});
  }}
}});

router.post('/login', (req, res, next) => {{
  passport.authenticate('local', (err, user, info) => {{
    if (err) return next(err);
    if (!user) return res.status(401).json({{ message: info.message || 'Login failed' }});
    req.login(user, (err) => {{
      if (err) return next(err);
      res.json(user);
    }});
  }})(req, res, next);
}});

// --- Google Auth ---
{google_auth_routes}

// --- Common ---
router.get('/user', (req, res) => {{
  if (req.isAuthenticated()) res.json(req.user);
  else res.status(401).json({{ message: 'Not authenticated' }});
}});

router.get('/logout', (req, res, next) => {{
  req.logout((err) => {{
    if (err) return next(err);
    res.json({{ message: 'Logged out' }});
  }});
}});

module.exports = router;
"""


    # --- Frontend Templates (MEAN / Angular v21) ---
    fe_deps = {
        "@angular/common": "^21.2.0",
        "@angular/compiler": "^21.2.0",
        "@angular/core": "^21.2.0",
        "@angular/forms": "^21.2.0",
        "@angular/platform-browser": "^21.2.0",
        "@angular/router": "^21.2.0",
        "rxjs": "~7.8.0",
        "tslib": "^2.3.0"
    }
    
    fe_dev_deps = {
        "@angular/build": "^21.2.7",
        "@angular/cli": "^21.2.7",
        "@angular/compiler-cli": "^21.2.0",
        "jsdom": "^28.0.0",
        "prettier": "^3.8.1",
        "typescript": "~5.9.2",
        "vitest": "^4.0.8"
    }

    if css_choice == "tailwind":
        fe_dev_deps.update({"tailwindcss": "^3.4.1", "postcss": "^8.4.35", "autoprefixer": "^10.4.18"})
    elif css_choice == "bulma":
        fe_deps.update({"bulma": "^1.0.1"})

    if use_matter:
        fe_deps.update({"matter-js": "^0.19.0"})
        fe_dev_deps.update({"@types/matter-js": "^0.19.6"})
    
    if use_anime:
        fe_deps.update({"animejs": "^3.2.2"})
        fe_dev_deps.update({"@types/animejs": "^3.1.12"})

    if use_confetti:
        fe_deps.update({"canvas-confetti": "^1.9.3"})
        fe_dev_deps.update({"@types/canvas-confetti": "^1.6.4"})

    if use_gsap:
        fe_deps.update({"gsap": "^3.15.0"})

    if use_three:
        fe_deps.update({"three": "^0.184.0"})
        fe_dev_deps.update({"@types/three": "^0.184.0"})

    if use_lenis:
        fe_deps.update({"@studio-freight/lenis": "^1.0.42"})


    fe_package_json = {
        "name": f"{project_name.lower()}-frontend",
        "version": "0.0.0",
        "scripts": {
            "ng": "ng",
            "start": "ng serve",
            "build": "node scripts/build-tasks.js prebuild && ng build && node scripts/build-tasks.js postbuild",
            "watch": "ng build --watch --configuration development",
            "test": "vitest"
        },
        "private": True,
        "dependencies": fe_deps,
        "devDependencies": fe_dev_deps
    }

    # Styles extension
    style_ext = "css"
    if css_choice == "scss": style_ext = "scss"

    fe_angular_json = {
        "version": 1,
        "projects": {
            "frontend": {
                "projectType": "application",
                "root": "",
                "sourceRoot": "src",
                "prefix": "app",
                "architect": {
                    "build": {
                        "builder": "@angular/build:application",
                        "options": {
                            "outputPath": "dist/frontend",
                            "index": "src/index.html",
                            "browser": "src/main.ts",
                            "tsConfig": "tsconfig.app.json",
                            "assets": [
                                { "glob": "**/*", "input": "public" }
                            ],
                            "styles": [f"src/styles.{style_ext}"]
                        },
                        "configurations": {
                            "production": {
                                "budgets": [
                                    { "type": "initial", "maximumWarning": "500kB", "maximumError": "1MB" },
                                    { "type": "anyComponentStyle", "maximumWarning": "4kB", "maximumError": "8kB" }
                                ],
                                "outputHashing": "all"
                            },
                            "development": {
                                "optimization": False,
                                "extractLicenses": False,
                                "sourceMap": True
                            }
                        },
                        "defaultConfiguration": "production"
                    },
                    "serve": {
                        "builder": "@angular/build:dev-server",
                        "options": {
                            "buildTarget": "frontend:build",
                            "port": int(fe_port)
                        },
                        "configurations": {
                            "production": {
                                "buildTarget": "frontend:build:production"
                            },
                            "development": {
                                "buildTarget": "frontend:build:development"
                            }
                        },
                        "defaultConfiguration": "development"
                    }
                }
            }
        }
    }

    # --- Tailwind Config (if selected) ---
    fe_tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      keyframes: {
        fadeIn: {
          'from': { opacity: '0', transform: 'translateY(20px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          'from': { opacity: '0', transform: 'scale(0.92)' },
          'to': { opacity: '1', transform: 'scale(1)' },
        },
        slideInLeft: {
          'from': { opacity: '0', transform: 'translateX(-30px)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInRight: {
          'from': { opacity: '0', transform: 'translateX(30px)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'scaleIn': 'scaleIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slideInLeft': 'slideInLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slideInRight': 'slideInRight 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }
    },
  },
  plugins: [],
}
"""
    fe_postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
"""

    fe_main_ts = """import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
"""

    fe_app_config_ts = """import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient()
  ]
};
"""



    auth_methods = ""
    if auth_choice != "None":
        auth_methods = f"""// --- Auth Methods ---
  login(credentials: any): Observable<any> {{
    return this.http.post<any>(`${{this.apiUrl}}/auth/login`, credentials).pipe(
      tap(user => this.currentUser.set(user))
    );
  }}

  // Redirect-based Google Login
  loginWithGoogle(): void {{
    window.location.href = `${{this.apiUrl}}/auth/google`;
  }}

  checkStatus(): Observable<any> {{
    return this.http.get<any>(`${{this.apiUrl}}/auth/user`).pipe(
      tap({{
        next: user => this.currentUser.set(user),
        error: () => this.currentUser.set(null)
      }})
    );
  }}

  logout(): void {{
    localStorage.removeItem('auth_token');
    this.currentUser.set(null);
  }}"""

    # --- ApiService Template (Simplified & General) ---
    fe_api_service_ts = f"""import {{ Injectable, inject, signal }} from '@angular/core';
import {{ HttpClient }} from '@angular/common/http';
import {{ Observable, tap }} from 'rxjs';

@Injectable({{
  providedIn: 'root'
}})
export class ApiService {{
  private http = inject(HttpClient);
  {"public currentUser = signal<any>(null);" if auth_choice != "None" else ""}

  // Dynamic API URL mapping
  private get apiUrl(): string {{
    const isProd = ('__PRODUCTION__' as string) === 'true';
    if (isProd) {{
      return '/api';
    }}
    return '/api';
  }}

  getData<T>(endpoint: string): Observable<T> {{
    return this.http.get<T>(`${{this.apiUrl}}/${{endpoint}}`);
  }}

  postData<T>(endpoint: string, body: any): Observable<T> {{
    return this.http.post<T>(`${{this.apiUrl}}/${{endpoint}}`, body);
  }}

  {auth_methods}
}}
"""


    fe_build_tasks_js = """const fs = require('fs');
const path = require('path');

function replaceEnv() {
  const file = path.join(__dirname, '..', 'src', 'app', 'services', 'api.service.ts');
  if (!fs.existsSync(file)) {
    console.log('[build-tasks] Skipping env replacement: ' + file + ' not found.');
    return;
  }

  let content = fs.readFileSync(file, 'utf8');
  content = content
    .replace('__PRODUCTION__', process.env.PRODUCTION || 'false')
    .replace('__PROD_BACKEND_URL__', process.env.PROD_BACKEND_URL || '')
    .replace('__PROD_FRONTEND_URL__', process.env.PROD_FRONTEND_URL || '');

  fs.writeFileSync(file, content);
  console.log('[build-tasks] Applied environment variables to ' + file);
}

function normalizeOutput() {
  const src = path.join(__dirname, '..', 'dist', 'frontend', 'browser');
  const dest = path.join(__dirname, '..', 'dist', 'frontend');

  if (fs.existsSync(src)) {
    console.log('[build-tasks] Normalizing output: moving ' + src + ' to ' + dest);
    fs.cpSync(src, dest, { recursive: true });
    fs.rmSync(src, { recursive: true });
    console.log('[build-tasks] Output normalization complete.');
  } else {
    console.log('[build-tasks] Skipping normalization: ' + src + ' not found.');
  }
}

const task = process.argv[2];
if (task === 'prebuild') replaceEnv();
else if (task === 'postbuild') normalizeOutput();
"""

    root_vercel_json = {
        "version": 2,
        "experimentalServices": {
            "frontend": {
                "entrypoint": "frontend",
                "routePrefix": "/",
                "framework": "angular"
            },
            "backend": {
                "entrypoint": "backend",
                "routePrefix": "/api"
            }
        },
        "headers": [
            {
                "source": "/(.*)",
                "headers": [
                    {
                        "key": "Content-Security-Policy",
                        "value": "frame-ancestors *"
                    },
                    {
                        "key": "Cross-Origin-Resource-Policy",
                        "value": "cross-origin"
                    }
                ]
            }
        ]
    }

    root_vercel_index = """const app = require('../backend/app');
// Vercel Serverless Function entry point
module.exports = app;
"""

    root_dev_launcher_js = """const net = require('net');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

function isPortAvailable(port) {
  const check = (host) => new Promise((resolve) => {
    const server = net.createServer();
    server.on('error', () => resolve(false));
    server.listen({ port, host, exclusive: true }, () => {
      server.close(() => resolve(true));
    });
  });
  
  return (async () => {
    const hosts = ['0.0.0.0', '::', '127.0.0.1', '::1'];
    for (const host of hosts) {
      if (!(await check(host))) return false;
    }
    return true;
  })();
}

async function getAvailablePort(startPort, name) {
  let port = parseInt(startPort);
  while (!(await isPortAvailable(port))) {
    console.log(`[Port Conflict] ${name} port ${port} is in use. Trying ${port + 1}...`);
    port++;
  }
  return port;
}

function parseEnv(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const content = fs.readFileSync(filePath, 'utf8');
  const env = {};
  content.split(/\\r?\\n/).forEach(line => {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine.startsWith('#')) return;
    
    const [key, ...valueParts] = trimmedLine.split('=');
    if (key && valueParts.length > 0) {
      env[key.trim()] = valueParts.join('=').trim();
    }
  });
  return env;
}

async function main() {
  const envPath = path.join(process.cwd(), '.env.local');
  const env = parseEnv(envPath);

  const defaultBePort = env.PORT || '3000';
  const defaultFePort = env.FRONTEND_PORT || '4200';

  console.log('Initializing Smart Dev Launcher (Ephemeral Mode)...');

  const finalBePort = await getAvailablePort(defaultBePort, 'Backend');
  const finalFePort = await getAvailablePort(defaultFePort, 'Frontend');

  const proxyConfig = {
    "/api": {
      "target": `http://localhost:${finalBePort}`,
      "secure": false,
      "changeOrigin": true
    },
    "/auth": {
      "target": `http://localhost:${finalBePort}`,
      "secure": false,
      "changeOrigin": true
    }
  };
  
  const proxyPath = path.join(process.cwd(), 'frontend', 'proxy.conf.json');
  fs.writeFileSync(proxyPath, JSON.stringify(proxyConfig, null, 2));
  console.log(`[Success] Generated temporary proxy: /api, /auth -> port ${finalBePort}`);

  const devArgs = [
    'concurrently',
    '--kill-others',
    '--prefix-colors', "blue,magenta",
    '--names', "backend,frontend",
    `"npx nodemon backend/bin/www"`,
    `"cd frontend && npx ng serve --port ${finalFePort} --proxy-config proxy.conf.json"`
  ];

  console.log(`Backend: http://localhost:${finalBePort}`);
  console.log(`Frontend: http://localhost:${finalFePort}`);
  console.log('---');

  const child = spawn('npx', devArgs, {
    stdio: 'inherit',
    shell: true,
    env: { ...process.env, PORT: finalBePort, FRONTEND_PORT: finalFePort }
  });

  child.on('exit', (code) => {
    try { fs.unlinkSync(proxyPath); } catch (e) {}
    process.exit(code);
  });
}

main().catch(err => {
  console.error('[Error] Launcher Error:', err);
  process.exit(1);
});
"""

    # --- Frontend Tooling Templates ---
    fe_tsconfig_json = {
        "compilerOptions": {
            "strict": True,
            "noImplicitOverride": True,
            "noPropertyAccessFromIndexSignature": True,
            "noImplicitReturns": True,
            "noFallthroughCasesInSwitch": True,
            "skipLibCheck": True,
            "isolatedModules": True,
            "experimentalDecorators": True,
            "importHelpers": True,
            "target": "ES2022",
            "module": "preserve",
            "moduleResolution": "bundler",
            "sourceMap": True
        },
        "angularCompilerOptions": {
            "enableI18nLegacyMessageIdFormat": False,
            "strictInjectionParameters": True,
            "strictInputAccessModifiers": True,
            "strictTemplates": True
        },
        "files": [],
        "references": [{ "path": "./tsconfig.app.json" }]
    }

    fe_prettierrc = """{
  "printWidth": 100,
  "singleQuote": true,
  "overrides": [
    {
      "files": "*.html",
      "options": {
        "parser": "angular"
      }
    }
  ]
}
"""

    fe_editorconfig = """# Editor configuration
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true

[*.ts]
quote_type = single
ij_typescript_use_double_quotes = false

[*.md]
max_line_length = off
trim_trailing_whitespace = false
"""

    fe_vscode_extensions = {
        "recommendations": [
            "angular.ng-template",
            "esbenp.prettier-vscode",
            "firsttris.vscode-jest-runner"
        ]
    }

    fe_readme = f"""# {project_name}

A full-stack MEAN application (MongoDB, Express, Angular, Node) generated with a premium portfolio template.

## Features
- **Frontend**: Angular v21 (Standalone, Signals)
- **Backend**: Node/Express with Graceful MongoDB
- **Security**: Iframe protection for portfolio embedding
- **Interactive**: Matter.js physics and Anime.js animations

## Development

### 1. Configure Environment
Ensure your `.env.local` file is updated with your `MONGODB_URI`.

### 2. Launch Full Stack
```bash
npm run dev
```
"""

    # Component imports and logic
    imports_list = ["Component", "signal", "inject", "OnInit"]
    if use_matter or use_anime or use_confetti:
        imports_list.extend(["viewChild", "ElementRef", "afterNextRender", "OnDestroy"])
    
    physics_imports = f"import {{ {', '.join(imports_list)} }} from '@angular/core';\nimport {{ ApiService }} from '../services/api.service';\n"
    if use_matter: physics_imports += "import * as Matter from 'matter-js';\n"
    if use_anime: physics_imports += "import anime from 'animejs';\n"
    if use_confetti: physics_imports += "import confetti from 'canvas-confetti';\n"
    if use_gsap: physics_imports += "import gsap from 'gsap';\nimport { ScrollTrigger } from 'gsap/ScrollTrigger';\n"
    if use_three: physics_imports += "import * as THREE from 'three';\n"
    if use_lenis: physics_imports += "import Lenis from '@studio-freight/lenis';\n"

    if use_gsap: physics_imports += "\ngsap.registerPlugin(ScrollTrigger);\n"


    physics_variables = ""
    if use_matter:
        physics_variables += "  private engine?: Matter.Engine;\n  private render?: Matter.Render;\n"
    
    physics_init_calls = ""
    if use_matter: physics_init_calls += "      this.initPhysics();\n"
    if use_anime: physics_init_calls += "      this.initAnimation();\n"
    if use_gsap: physics_init_calls += "      this.initGSAP();\n"
    if use_three: physics_init_calls += "      this.initThreeJS();\n"
    if use_lenis: physics_init_calls += "      this.initLenis();\n"


    physics_logic = ""
    if use_matter or use_anime or use_confetti:
        physics_logic += f"""
  private container = viewChild<ElementRef<HTMLDivElement>>('scene');
  private card = viewChild<ElementRef<HTMLDivElement>>('card');
{physics_variables}
  private lenis?: Lenis;

  constructor() {{
    afterNextRender(() => {{
{physics_init_calls}
      if ({'true' if use_matter or use_three else 'false'}) window.addEventListener('resize', this.handleResize);
    }});
  }}

  ngOnDestroy() {{
    window.removeEventListener('resize', this.handleResize);
    {"if (this.render) { Matter.Render.stop(this.render); if (this.render.canvas.parentNode) { this.render.canvas.parentNode.removeChild(this.render.canvas); } }" if use_matter else ""}
    {"if (this.engine) Matter.Engine.clear(this.engine);" if use_matter else ""}
    { "if (this.lenis) this.lenis.destroy();" if use_lenis else "" }
    { "ScrollTrigger.getAll().forEach(t => t.kill());" if use_gsap else "" }
  }}

  private handleResize = () => {{
    const el = this.container()?.nativeElement;
    if (el && {'this.render' if use_matter else 'false'}) {{
      {( 'this.render.canvas.width = el.clientWidth; this.render.options.width = el.clientWidth;' if use_matter else '')}
    }}
  }};

"""
    else:
        physics_logic = ""
    if use_anime:
        physics_logic += """
  private initAnimation() {
    const el = this.card()?.nativeElement;
    if (el) {
      anime({
        targets: el,
        scale: [1, 1.02],
        direction: 'alternate',
        easing: 'easeInOutSine',
        duration: 1400,
        loop: true
      });
    }
  }
"""
    if use_gsap:
        physics_logic += """
  private initGSAP() {
    gsap.from(".glass", {
      y: 100,
      opacity: 0,
      duration: 1.2,
      ease: "power4.out",
      stagger: 0.2,
      scrollTrigger: {
        trigger: ".glass",
        start: "top 90%"
      }
    });
  }
"""
    if use_lenis:
        physics_logic += """
  private initLenis() {
    this.lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    const raf = (time: number) => {
      this.lenis?.raf(time);
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  }
"""
    if use_three:
        physics_logic += """
  private initThreeJS() {
    const el = this.container()?.nativeElement;
    if (!el) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, el.clientWidth / 220, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(el.clientWidth, 220);
    el.appendChild(renderer.domElement);

    const geometry = new THREE.TorusKnotGeometry(10, 3, 100, 16);
    const material = new THREE.MeshNormalMaterial();
    const torusKnot = new THREE.Mesh(geometry, material);
    scene.add(torusKnot);

    camera.position.z = 30;

    const animate = () => {
      requestAnimationFrame(animate);
      torusKnot.rotation.x += 0.01;
      torusKnot.rotation.y += 0.01;
      renderer.render(scene, camera);
    };
    animate();
  }
"""
    if use_matter:
        physics_logic += """
  private initPhysics() {
    const el = this.container()?.nativeElement;
    if (!el) return;

    this.engine = Matter.Engine.create();
    this.render = Matter.Render.create({
      element: el,
      engine: this.engine,
      options: {
        width: el.clientWidth,
        height: 220,
        background: 'transparent',
        wireframes: false
      }
    });

    const ground = Matter.Bodies.rectangle(el.clientWidth / 2, 210, el.clientWidth, 20, { 
      isStatic: true,
      render: { fillStyle: '#d1d5db' }
    });
    
    const ball = Matter.Bodies.circle(80, 30, 20, { 
      restitution: 0.85,
      render: { fillStyle: '#ffb347' }
    });

    Matter.World.add(this.engine.world, [ground, ball]);
    
    const runner = Matter.Runner.create();
    Matter.Runner.run(runner, this.engine);
    Matter.Render.run(this.render);
  }
"""
    fe_app_ts = f"""import {{ Component }} from '@angular/core';
import {{ RouterOutlet }} from '@angular/router';

@Component({{
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet></router-outlet>',
}})
export class App {{}}
"""

    fe_app_routes_ts = f"""import {{ Routes }} from '@angular/router';
import {{ HomeComponent }} from './home/home.component';
{ "import { LoginComponent } from './login/login.component';" if auth_choice != "None" else "" }
{ "import { DashboardComponent } from './dashboard/dashboard.component';" if auth_choice != "None" else "" }

export const routes: Routes = [
  {{ path: '', redirectTo: 'home', pathMatch: 'full' }},
  {{ path: 'home', component: HomeComponent }},
  { "{ path: 'login', component: LoginComponent }," if auth_choice != "None" else "" }
  { "{ path: 'dashboard', component: DashboardComponent }," if auth_choice != "None" else "" }
];
"""

    fe_home_component_ts = f"""{physics_imports}
@Component({{
  selector: 'app-home',
  standalone: true,
  imports: [],
  templateUrl: './home.component.html',
  styleUrl: './home.component.{style_ext}'
}})
export class HomeComponent implements OnInit {{
  private api = inject(ApiService);
  protected readonly title = signal('{project_name}');
  
  ngOnInit() {{
    this.api.getData('health').subscribe((res: any) => console.log('API Status:', res));
  }}

  {physics_logic}
}}
"""

    # Template logic (Tailwind vs Bulma vs Plain)
    card_classes = "box" if css_choice == "bulma" else "p-8 bg-white rounded-xl shadow-2xl border border-gray-100"
    container_classes = "container" if css_choice == "bulma" else "max-w-4xl mx-auto p-4 flex items-center justify-center min-h-screen"
    scene_classes = "mt-4 border rounded-lg bg-gray-50 h-[220px]" if css_choice == "tailwind" else "scene mt-4"

    fe_home_html = f"""<main class="{container_classes}">
  <div #card class="{card_classes} glass text-center">
    <div class="glass-orb absolute -top-20 -left-20 w-40 h-40 bg-blue-400/20 blur-3xl rounded-full"></div>
    <div class="glass-orb absolute -bottom-20 -right-20 w-40 h-40 bg-purple-400/20 blur-3xl rounded-full"></div>
    
    <p class="text-xs uppercase tracking-widest text-gray-400 mb-2 font-medium">Portfolio Showcase</p>
    <h1 class="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
      {project_name}
    </h1>
    <p class="text-gray-500 mb-8 max-w-md mx-auto leading-relaxed">
      A high-performance MEAN application featuring standalone components, Signals, and premium interactive elements.
    </p>
    
    <div class="flex gap-4 justify-center mb-10">
      <button class="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200">
        Get Started
      </button>
      <button class="px-6 py-3 bg-white text-gray-700 border border-gray-200 rounded-full font-semibold hover:bg-gray-50 transition-all">
        View Source
      </button>
    </div>

    <div #scene class="{scene_classes} transform hover:scale-[1.01] transition-transform cursor-pointer">
      <!-- Interactive Scene -->
    </div>
  </div>
</main>
"""


    fe_index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{project_name}</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
  <script>
    (function() {{
      console.log('🚀 [' + {PROJECT_NAME_VAR} + '] Client script active.');
      if (window.parent !== window) {{
        console.log('🚀 [' + {PROJECT_NAME_VAR} + '] Embedded in iframe. Sending handshake...');
        window.parent.postMessage({{ type: 'CHECK_IN', project: {PROJECT_NAME_VAR} }}, '*');
      }} else {{
        console.log('🚀 [' + {PROJECT_NAME_VAR} + '] Running standalone.');
      }}
    }})();
  </script>
  { '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.min.css">' if css_choice == 'bulma' else '' }
</head>
<body class="bg-slate-50">
  <app-root></app-root>
</body>
</html>
"""

    # --- Write Backend ---
    (backend_root / "package.json").write_text(json.dumps(be_package_json, indent=2), encoding='utf-8')
    (backend_root / "app.js").write_text(be_app_js, encoding='utf-8')
    (backend_root / "bin").mkdir()
    (backend_root / "bin" / "www").write_text(be_www, encoding='utf-8')
    (backend_root / "routes").mkdir()
    (backend_root / "routes" / "index.js").write_text(be_routes_index, encoding='utf-8')
    if auth_choice != "None":
        (backend_root / "routes" / "auth.js").write_text(be_auth_routes, encoding='utf-8')
    
    (backend_root / "models").mkdir()
    if auth_choice != "None":
        (backend_root / "models" / "user.js").write_text(be_user_model, encoding='utf-8')
    
    if auth_choice in ["Local", "Both"]:
        (backend_root / "config").mkdir()
        (backend_root / "config" / "passport.js").write_text(be_passport_js, encoding='utf-8')

    
    if fe_hosting == "vercel" or be_hosting == "vercel":
        # 1. API Bridge / Entry Point for Vercel Functions
        (project_root / "api").mkdir(exist_ok=True)
        (project_root / "api" / "index.js").write_text(root_vercel_index, encoding='utf-8')

        # 2. Unified Vercel Configuration
        (project_root / "vercel.json").write_text(json.dumps(root_vercel_json, indent=2), encoding='utf-8')


    # --- Write Frontend Configs ---
    (frontend_root / "package.json").write_text(json.dumps(fe_package_json, indent=2), encoding='utf-8')
    (frontend_root / "angular.json").write_text(json.dumps(fe_angular_json, indent=2), encoding='utf-8')
    (frontend_root / "tsconfig.json").write_text(json.dumps(fe_tsconfig_json, indent=2), encoding='utf-8')
    
    scripts_dir = frontend_root / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "build-tasks.js").write_text(fe_build_tasks_js, encoding='utf-8')
    (frontend_root / "tsconfig.app.json").write_text(json.dumps({
        "extends": "./tsconfig.json",
        "compilerOptions": { "outDir": "./out-tsc/app", "types": [] },
        "include": ["src/**/*.ts"]
    }, indent=2), encoding='utf-8')
    (frontend_root / ".prettierrc").write_text(fe_prettierrc, encoding='utf-8')
    (frontend_root / ".editorconfig").write_text(fe_editorconfig, encoding='utf-8')
    
    vscode_dir = frontend_root / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "extensions.json").write_text(json.dumps(fe_vscode_extensions, indent=2), encoding='utf-8')

    if css_choice == "tailwind":
        (frontend_root / "tailwind.config.js").write_text(fe_tailwind_config, encoding='utf-8')
        (frontend_root / "postcss.config.js").write_text(fe_postcss_config, encoding='utf-8')
    
    (frontend_root / "public").mkdir()
    src_root = frontend_root / "src"
    src_root.mkdir()
    (src_root / "index.html").write_text(fe_index_html, encoding='utf-8')
    
    # Styles
    styles_content = "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n" if css_choice == "tailwind" else "/* Global Styles */\n"
    styles_content += """
.glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

.glass-orb {
  animation: float 10s ease-in-out infinite;
}
"""
    (src_root / f"styles.{style_ext}").write_text(styles_content, encoding='utf-8')

    (src_root / "main.ts").write_text(fe_main_ts, encoding='utf-8')
    
    app_dir = src_root / "app"
    app_dir.mkdir()
    (app_dir / "app.ts").write_text(fe_app_ts, encoding='utf-8')
    (app_dir / "app.config.ts").write_text(fe_app_config_ts, encoding='utf-8')
    (app_dir / "app.routes.ts").write_text(fe_app_routes_ts, encoding='utf-8')

    # Home Component
    home_dir = app_dir / "home"
    home_dir.mkdir()
    (home_dir / "home.component.ts").write_text(fe_home_component_ts, encoding='utf-8')
    (home_dir / "home.component.html").write_text(fe_home_html, encoding='utf-8')
    (home_dir / f"home.component.{style_ext}").write_text("/* Home Styles */\n", encoding='utf-8')

    if auth_choice != "None":
        # Login Component
        login_dir = app_dir / "login"
        login_dir.mkdir()
        login_ts = f"""import {{ Component, inject, signal }} from '@angular/core';
import {{ Router }} from '@angular/router';
import {{ ApiService }} from '../services/api.service';
import {{ FormsModule }} from '@angular/forms';

@Component({{
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="container p-4 max-w-md mx-auto min-h-screen flex items-center">
      <div class="p-8 bg-white rounded-xl shadow-2xl border w-full glass">
        <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
        
        <div class="space-y-4">
          <button (click)="loginWithGoogle()" 
                  class="w-full p-3 bg-white border border-gray-300 rounded-lg flex items-center justify-center hover:bg-gray-50 transition-colors">
            <img src="https://www.google.com/favicon.ico" class="w-5 h-5 mr-2" alt="Google">
            Sign in with Google
          </button>
          
          <div class="relative flex items-center justify-center py-2">
            <div class="border-t w-full"></div>
            <span class="bg-white px-2 text-gray-500 text-sm absolute">or email</span>
          </div>

          <input [(ngModel)]="email" type="email" placeholder="Email" class="w-full p-3 border rounded-lg">
          <input [(ngModel)]="password" type="password" placeholder="Password" class="w-full p-3 border rounded-lg">
          
          <button (click)="login()" 
                  class="w-full p-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors">
            Sign In
          </button>
        </div>
      </div>
    </div>
  `
}})
export class LoginComponent {{
  private api = inject(ApiService);
  private router = inject(Router);
  email = '';
  password = '';

  login() {{
    this.api.login({{ email: this.email, password: this.password }}).subscribe({{
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => alert(err.error?.message || 'Login failed')
    }});
  }}

  loginWithGoogle() {{
    this.api.loginWithGoogle();
  }}
}}
"""
        (login_dir / "login.component.ts").write_text(login_ts, encoding='utf-8')

        # Dashboard Component
        dash_dir = app_dir / "dashboard"
        dash_dir.mkdir()
        dash_ts = f"""import {{ Component, inject, OnInit }} from '@angular/core';
import {{ ApiService }} from '../services/api.service';
import {{ Router }} from '@angular/router';

@Component({{
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <div class="container p-8 max-w-4xl mx-auto">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">Dashboard</h1>
        <button (click)="logout()" class="text-red-600 font-semibold">Logout</button>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 bg-white rounded-xl shadow border glass">
          <h3 class="text-gray-500 text-sm uppercase">User</h3>
          <p class="text-xl font-semibold">{{{{ api.currentUser()?.email }}}}</p>
        </div>
      </div>
    </div>
  `
}})
export class DashboardComponent implements OnInit {{
  public api = inject(ApiService);
  private router = inject(Router);

  ngOnInit() {{
    this.api.checkStatus().subscribe({{
      error: () => this.router.navigate(['/login'])
    }});
  }}

  logout() {{
    this.api.logout();
    this.router.navigate(['/home']);
  }}
}}
"""
        (dash_dir / "dashboard.component.ts").write_text(dash_ts, encoding='utf-8')

    # Services
    services_dir = app_dir / "services"
    services_dir.mkdir()
    (services_dir / "api.service.ts").write_text(fe_api_service_ts, encoding='utf-8')

    # --- Env File (Root Only) ---
    env_content = f"""PROJECT_NAME={project_name}
PORT={be_port}
FRONTEND_PORT={fe_port}
MONGODB_URI=mongodb://localhost:27017/{project_name}

# --- Production Configuration ---
PRODUCTION=false

# --- Back-End Deployment ---
PROD_BACKEND_URL=
PROD_FRONTEND_URL=

# --- Auth Secrets ---
{ "SESSION_SECRET=" + (os.urandom(16).hex()) if auth_choice in ["Local", "Both", "Google"] else "" }
{ "GOOGLE_CLIENT_ID=" if auth_choice in ["Google", "Both"] else "" }
{ "GOOGLE_CLIENT_SECRET=" if auth_choice in ["Google", "Both"] else "" }

# --- API Keys ---
OPENAI_API_KEY=
"""

    # Note: We write this again later after Vercel initialization to ensure it's preserved.
    (project_root / ".env.local").write_text(env_content, encoding='utf-8')

    # --- Root Files ---
    root_package_json = {
        "name": project_slug,
        "version": "1.0.0",
        "scripts": {
            "dev": "node scripts/dev-launcher.js",
            "build": "cd frontend && npm install && npm run build",
            "postinstall": "npm install --prefix backend && npm install --prefix frontend",
            "start": "node start-dev.js"
        },
        "dependencies": {
            "express": "^4.19.2",
            "mongoose": "^8.0.0",
            "cors": "^2.8.5",
            "dotenv": "^16.4.5",
            "helmet": "^7.1.0",
            "morgan": "~1.10.0",
            "cookie-parser": "~1.4.6",
            "concurrently": "^8.2.2",
            "nodemon": "^3.1.0"
        }
    }
    (project_root / "package.json").write_text(json.dumps(root_package_json, indent=2), encoding='utf-8')
    scripts_root = (project_root / "scripts")
    scripts_root.mkdir(exist_ok=True)
    (scripts_root / "dev-launcher.js").write_text(root_dev_launcher_js, encoding='utf-8')
    (project_root / ".gitignore").write_text("node_modules/\ndist/\n.env.local\n.angular/\n.vscode/\n", encoding='utf-8')
    (project_root / "README.md").write_text(fe_readme, encoding='utf-8')

    # Emergency Deletion Script
    delete_project_py = f"""import os
import sys
import subprocess
import time
import shutil

def main():
    project_name = "{project_name}"
    project_path = os.path.dirname(os.path.abspath(__file__))

    print(f"\\n--- EMERGENCY DELETION: {{project_name}} ---")
    print(f"Target Path: {{project_path}}\\n")

    # Check if we are inside the directory
    if os.getcwd() == project_path:
        print("WARNING: You are currently INSIDE the project directory in your terminal.")
        print("I will change the current directory to '..' to allow full deletion.\\n")
        os.chdir('..')

    # 3 Warnings
    input(f"WARNING 1/3: This will PERMANENTLY delete everything in {{project_path}}. Press Enter to continue...")
    input("WARNING 2/3: All code, git history, and node_modules will be GONE. Press Enter to continue...")
    input(f"WARNING 3/3: FINAL CONFIRMATION. You are about to destroy {{project_name}} at {{project_path}}. Press Enter to continue...")

    # Final verification
    confirm = input(f"\\nTo confirm, type the exact project name '{{project_name}}': ").strip()

    if confirm == project_name:
        print("\\nOK. Initiating force-deletion...")
        
        # 1. Try to delete contents first
        for item in os.listdir(project_path):
            if item == 'delete-project.py': continue
            item_path = os.path.join(project_path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
                print(f"   Deleted: {{item}}")
            except Exception as e:
                print(f"   [!] Could not delete {{item}}: {{e}}")

        # 2. Spawn a background process to kill this script and try to remove the root and itself
        print("\\nAttempting to remove root directory in 1 second...")
        # We use a more aggressive PowerShell command that retries and ignores errors
        cmd = f"Start-Sleep -s 1; 1..5 | % {{{{ Remove-Item -Path '{{project_path}}' -Recurse -Force -ErrorAction SilentlyContinue; if (!(Test-Path '{{project_path}}')) {{{{ break }}}}; Start-Sleep -s 1 }}}}"
        subprocess.Popen(["powershell", "-Command", cmd], shell=True)
        sys.exit(0)
    else:
        print("\\nName mismatch. Deletion cancelled.")

if __name__ == '__main__':
    main()
"""
    (project_root / "delete-project.py").write_text(delete_project_py, encoding='utf-8')

    # AI Config
    ai_rules_common = f"""## Agent Operational Directives
- **File Deletions**: When deleting multiple files, do so one at a time.
- **Syntax**: Always use standard Windows PowerShell syntax (e.g., `Remove-Item`, `New-Item`).
- **Persistence**: If a command fails, try alternative PowerShell methods before giving up.
- **Privacy**: Never expose the `.env.local` file content in logs.
"""

    if ai_choice == "Agents.md":
        (project_root / "AGENTS.md").write_text(f"""# {project_name} - Agent Instructions

This project follows a decoupled MEAN stack architecture.

## Architecture
- **Frontend**: Angular v21+ (located in `/frontend`)
- **Backend**: Node/Express + Mongoose (located in `/backend`)

## Portfolio Requirements
- **Security**: Iframe headers are set to allow embedding in `carter-portfolio.fyi`.
- **CSS**: Using {css_choice}.
- **Features**: {", ".join([f for f, v in [("Physics (Matter)", use_matter), ("Animations (Anime)", use_anime), ("Confetti", use_confetti)] if v]) or "Standard"}.
- **Vercel Watcher**: Persistent sync enabled via `pre-push` git hook.

## Agent Rules
- Always maintain the iframe security headers in `backend/app.js`.
- Prefer Signals for Angular state.
- Use standalone components.
- **Environment**: If you modify the root `.env.local`, remind the user to `git push` to sync with Vercel.

{ai_rules_common}
""", encoding='utf-8')
    elif ai_choice == "Cursor":
        (project_root / ".cursorrules").write_text(f"# {project_name} Cursor Rules\n\n- Angular 21 (Signals, standalone).\n- Maintain iframe CSP headers in backend/app.js.\n\n{ai_rules_common}\n", encoding='utf-8')
    elif ai_choice == "Claude":
        claude_dir = project_root / ".claudecode"
        claude_dir.mkdir()
        (claude_dir / "memory.md").write_text(f"""# Project Memory: {project_name}

## Summary
Decoupled MEAN Stack (Angular {fe_port} / Express {be_port}).

## Tech Stack
- Frontend: Angular v21, Matter-js, Animejs.
- Backend: Express, Mongoose, Helmet.

## Directives
{ai_rules_common}
""", encoding='utf-8')

    # --- Host-Specific Environment Prep ---
    if fe_hosting == "vercel" or be_hosting == "vercel":
        print("\n--- Preparing Vercel Environment ---")
        try:
            # Merged content logic...
            
            existing_env = {}
            env_file = project_root / ".env.local"
            if env_file.exists():
                for line in env_file.read_text(encoding='utf-8').splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        existing_env[k.strip()] = v.strip()
            
            for line in env_content.splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    existing_env[k.strip()] = v.strip()
            
            # Write back the merged content
            merged_content = ""
            merged_content += f"PROJECT_NAME={existing_env.get('PROJECT_NAME', project_name)}\n"
            merged_content += f"PORT={existing_env.get('PORT', be_port)}\n"
            merged_content += f"FRONTEND_PORT={existing_env.get('FRONTEND_PORT', fe_port)}\n"
            merged_content += f"MONGODB_URI={existing_env.get('MONGODB_URI', '')}\n\n"
            merged_content += "# --- Production Configuration ---\n"
            merged_content += f"PRODUCTION={existing_env.get('PRODUCTION', 'false')}\n\n"
            merged_content += "# --- Back-End Deployment ---\n"
            merged_content += f"PROD_BACKEND_URL={existing_env.get('PROD_BACKEND_URL', '')}\n"
            merged_content += f"PROD_FRONTEND_URL={existing_env.get('PROD_FRONTEND_URL', '')}\n\n"
            
            if auth_choice != "None":
                merged_content += f"SESSION_SECRET={existing_env.get('SESSION_SECRET', '')}\n"
            if auth_choice in ["Google", "Both"]:
                merged_content += f"GOOGLE_CLIENT_ID={existing_env.get('GOOGLE_CLIENT_ID', '')}\n"
                merged_content += f"GOOGLE_CLIENT_SECRET={existing_env.get('GOOGLE_CLIENT_SECRET', '')}\n"
            
            merged_content += "\n# --- Vercel Managed Variables ---\n"
            for k, v in existing_env.items():
                if k not in ['PROJECT_NAME', 'PORT', 'FRONTEND_PORT', 'MONGODB_URI', 'PRODUCTION', 'PROD_BACKEND_URL', 'PROD_FRONTEND_URL', 'SESSION_SECRET', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']:
                    merged_content += f"{k}={v}\n"
            
            env_file.write_text(merged_content, encoding='utf-8')

            # 1. Link the project
            subprocess.run(["vercel", "link", "--yes"], cwd=project_root, check=True, shell=True)
            
            # 2. Sync variables
            vars_added = 0
            keys = list(existing_env.keys())
            for i, key in enumerate(keys, 1):
                if key in ['PROJECT_NAME', 'PORT', 'FRONTEND_PORT', 'MONGODB_URI', 'PRODUCTION', 'PROD_BACKEND_URL', 'PROD_FRONTEND_URL', 'SESSION_SECRET', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']:
                    print(f"   [{i}/{len(keys)}] Adding {key} to Vercel Vault...", end="", flush=True)
                    # We use powershell to avoid shell escaping issues on Windows
                    res = subprocess.run([
                        "powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", 
                        f"vercel env add {key} production --yes"
                    ], cwd=project_root, input=existing_env[key], text=True, capture_output=True)
                    
                    if res.returncode == 0:
                        print(" [OK]")
                        vars_added += 1
                    else:
                        print(f" [FAIL] ({res.stderr.strip()})")
            
            print(f"[Success] {vars_added} variables synced to Vercel.")


        except subprocess.CalledProcessError as e:
            print(f"Warning: Vercel preparation encountered an issue: {e}")
    try:
        subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
        print("Initialized Git repository.")
        
        # --- Vercel Watcher (Git Hook) ---
        if fe_hosting == "vercel" or be_hosting == "vercel":
            sync_env_py = """import os
import subprocess
from pathlib import Path

def sync_vercel_env():
    \"\"\"Reads the root .env.local and syncs each variable to the Vercel Production vault.\"\"\"
    candidates = [Path('.env.local'), Path('.env')]
    env_path = next((c for c in candidates if c.exists()), None)
    
    if not env_path:
        print(">> No environment file found. Skipping sync.")
        return

    print(f">> Vercel Watcher: Syncing {env_path.name} to Production Vault...")
    
    try:
        env_vars = {}
        with open(env_path, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
        
        if not env_vars:
            print(">> Environment file is empty.")
            return

        keys = list(env_vars.keys())
        for i, key in enumerate(keys, 1):
            val = env_vars[key]
            print(f"   [{i}/{len(keys)}] Syncing {key}...", end="", flush=True)
            
            # 1. Remove existing
            subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", f"vercel env rm {key} production --yes"],
                capture_output=True
            )
            
            # 2. Add new value via stdin
            res = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", f"vercel env add {key} production --yes"],
                input=val, text=True, capture_output=True
            )
            
            if res.returncode == 0:
                print(" [OK]")
            else:
                print(f" [FAIL] (Error: {res.stderr.strip()})")

        print("OK: Vercel Vault updated successfully.")
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_vercel_env()
"""
            (project_root / "sync-env.py").write_text(sync_env_py, encoding='utf-8')

            pre_push_hook = """#!/bin/sh
# Vercel Watcher Hook
# Syncs local .env.local to Vercel Vault before every push.

echo \"Vercel Watcher: Checking environment status...\"
python sync-env.py

# Always allow the push to continue
exit 0
"""
            hook_path = project_root / ".git" / "hooks" / "pre-push"
            hook_path.write_text(pre_push_hook, encoding='utf-8')

    except Exception as e:
        print(f"Warning: Git/Hook initialization issue: {e}")

    # --- NPM Install ---
    print("\nInstalling dependencies (this may take a few minutes)...")
    try:
        print(f"[{project_name}] Backend npm install...")
        subprocess.run(["npm", "install"], cwd=backend_root, check=True, shell=True)
        print(f"[{project_name}] Frontend npm install...")
        subprocess.run(["npm", "install"], cwd=frontend_root, check=True, shell=True)
        print("Success: Dependencies installed successfully.")
    except Exception as e:
        print(f"Warning: npm install failed: {e}")
    
    # Root install for concurrently
    try:
        print(f"[{project_name}] Root npm install (concurrently)...")
        subprocess.run(["npm", "install"], cwd=project_root, check=True, shell=True)
    except Exception as e:
        print(f"Warning: root npm install failed: {e}")

    print("\nProject creation complete!")
    print(f"Location: {project_root}")
    print("\nNext steps:")
    print(f"  cd {project_name}")
    print(f"  npm run dev")

if __name__ == "__main__":
    main()
