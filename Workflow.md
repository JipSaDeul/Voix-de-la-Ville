# MVP Development Workflow of "VdV(Voix de la Ville)"

## Phase 1: Foundation (Week 1)

- [x] Set up Django project + REST Framework  
- [x] Define core models: User, Report, Vote, Comment, ReportCategory  
- [x] Set up Django Admin for staff moderation  
- [x] Configure django-allauth or simple login/signup  
- [x] Enable file uploads for report images  
- [x] Configure CORS + simple REST API endpoints  

## Phase 2: User Functions (Week 2)

- [ ] POST `/api/reports/`: Create a report with image, GPS, text  
- [ ] GET `/api/reports/`: List & filter reports  
- [ ] POST `/api/votes/`: Upvote a report (one per user)  
- [ ] Multilingual support: integrate `argos-translate` to auto-translate  
- [ ] NLP categorization: `spaCy` rule-based classifier for categories (optional fallback to manual)  

## Phase 3: Admin & Feedback (Week 3)

- [ ] Django Admin setup: Staff can change report status  
- [ ] Add status update notifications (email or frontend-polling)  
- [ ] Add moderation for comments  
- [ ] API: municipal staff can comment via admin or frontend  
- [ ] Map integration (using `leaflet.js` or `mapbox`): report locations on map  

## Phase 4: Polish & Deploy (Week 4)

- [ ] Frontend UI: simple mobile-first UI using React/Next.js or template  
- [ ] Translate UI strings (i18n: French, English)  
- [ ] Test workflows: report creation → NLP → admin view → resolution  
- [ ] Deploy with Docker (optional), SQLite/PostgreSQL + static file handling
