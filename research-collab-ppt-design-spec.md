# Research Collaboration System: PPT Design Specification

## 1. Direction & Rationale

**Style: Swiss Design (International Typographic Style)**
**Essence:** Mathematical precision, objective clarity, and structural logic.

**Rationale:**
- **Academic Rigor:** The grid-based layout mirrors the structured nature of database architecture and system design.
- **Clarity for Complexity:** High-contrast Black/White with Swiss Red accents ensures complex ER diagrams and performance metrics are legible.
- **Objective Tone:** The lack of decoration focuses the audience entirely on the technical achievements and research outcomes.

**Key Characteristics:**
- **Strict Grid System:** 6-column modular grid for aligning architecture diagrams and code snippets.
- **Typography-First:** Helvetica Neue (or Arial) used for hierarchy; size indicates importance, not color.
- **Functional Color:** predominantly White/Gray/Black for the "academic" feel; Red is used *only* for critical data points (alerts, primary metrics).
- **Asymmetric Balance:** Titles flush left, generous whitespace (40-60%) to prevent visual fatigue.

**Reference:** MIT Media Lab reports, Dieter Rams' design principles, classic Swiss architectural posters.

---

## 2. Slide Templates (1280×720px)

**General Rules:**
- **Max Content:** 7 lines of text per slide. If content >7 lines, split into "Part 1/2" or "Overview/Detail".
- **Margins:** 120px (Left/Right), 80px (Top/Bottom).
- **Grid:** 6 columns (240px wide) or 12 columns (100px wide).

### 1. Title Slide (Academic Formal)
**Purpose:** Project introduction.
**Layout:** Asymmetric. Title and metadata flush-left in the first 4 columns.
**Typography:**
- **Title:** 72px Bold, Line-height 1.1, Black. Top margin 160px.
- **Subtitle:** 36px Medium, Gray #333. 24px spacing below title.
- **Metadata:** 24px Regular, Gray #666. "Course Name | Date | Author". Bottom-left aligned (80px margin).
**Visuals:** Optional thin red horizontal line (4px height) separating title and subtitle.
**Background:** Pure White.

### 2. Content Slide (System Architecture)
**Purpose:** Explaining system components/flow.
**Layout:** 2-Column Split.
- **Left (Text):** 38% width. Title (54px), Bullet points (24px).
- **Right (Visual):** 62% width. Diagram area.
**Typography:**
- Title: 54px Bold, flush left top.
- Body: 24px Regular, max 6 lines. Bullet points use simple hyphens "- ".
**Visuals:** Diagram placed on pixel-perfect grid. No shadows on boxes. 1px borders.
**Pagination:** If architecture description is long, use "Architecture: Overview" then "Architecture: Details".

### 3. Data Slide (Performance Metrics)
**Purpose:** Comparing query speeds (MongoDB vs Neo4j).
**Layout:** Top-Bottom.
- **Header:** Title (54px) + Key Insight (28px Bold, Red) in top 160px.
- **Chart Area:** Central 500px height.
**Visual Pattern:**
- **Bar Chart:** Horizontal bars. Black for baseline, Red for "winner/fastest".
- **Labels:** 22px Medium.
- **Axis:** Minimal. 1px gray lines.
- **Data Labels:** 32px Bold, placed at end of bars.
**Density:** If >4 metrics, use 2 slides.

### 4. Comparison Slide (Database Selection)
**Purpose:** Why NoSQL vs SQL? MongoDB vs Cassandra.
**Layout:** 2 or 3 columns.
- **Col 1:** Criteria (Scalability, Model, Query).
- **Col 2/3:** Technologies.
**Typography:**
- **Headers:** 28px Bold, Underlined (2px Black).
- **Body:** 22px Regular (High Density).
- **Contrast:** Alternate row background (very light gray #F3F4F5) for readability.
**Pagination:** Split by category (e.g., "Comparison: Data Model" / "Comparison: Performance") if table is deep.

### 5. Quote/Key Finding Slide
**Purpose:** Highlighting a major research outcome.
**Layout:** Centered or Golden Ratio (text at 38% line).
**Typography:**
- **Quote:** 48px Light Italic (or Regular).
- **Attribution:** 24px Bold, Red.
**Visuals:** Large "Swiss" quotation marks (120px, Light Gray) as background texture (opacity 10%).

### 6. Section Break
**Purpose:** Transition between topics (e.g., "Implementation Phase").
**Layout:** Solid Color Block or Minimal White.
- **Option A:** Full Swiss Red background, White text (72px Bold), centered.
- **Option B:** Pure White, Huge Number (200px Black) top-left, Section Title (54px) bottom-right.

### 7. Custom: Entity Relationship / Data Model
**Purpose:** Displaying complex JSON or Graph schemas.
**Layout:** Maximized Content.
- **Title:** Small (36px) top-left.
- **Canvas:** Full width (minus 80px margins).
**Typography:**
- **Code/JSON:** Monospace font (Courier/Roboto Mono), 20px.
- **Annotations:** 18px Red, with thin lines pointing to schema elements.
**Visuals:** Gray background panels (#F3F4F5) for code blocks.

### 8. Closing Slide
**Purpose:** Conclusion & Q&A.
**Layout:** Asymmetric Left-Aligned.
- **Heading:** "Conclusion" (54px).
- **Summary:** 3 key bullet points (28px).
- **Contact:** Bottom-right block. "Github Repo | Email".
**Visuals:** Final strong red accent (square 80x80px) in bottom-right corner.

---

## 3. Visual Guidelines

**Color Usage:**
- **Dominant:** White (Background), Black (Text/Lines).
- **Structure:** Light Grays (#CCCCCC, #F3F4F5) for table rows, code backgrounds, secondary text.
- **Accent:** Swiss Red (#E30220) strictly for:
  - Critical data points (the "highest throughput").
  - Active navigation state.
  - Alerts/Warnings.
  - **Ratio:** 85% White, 10% Black, 5% Red.

**Typography & Text:**
- **Family:** Helvetica Neue, Arial, or Inter.
- **Weights:** Bold (700) for Headers, Regular (400) for Body.
- **Alignment:** ALWAYS Flush Left. NEVER Justified.
- **Size Validation:**
  - Body: 24px (Standard), 22px (Dense/Code).
  - Captions: 16px.
  - **Never** go below 16px.

**Imagery & Icons:**
- **Photos:** Black & White filters preferred for team/setup photos. High contrast.
- **Icons:** SVG Only. Simple geometric outlines (Lucide/Heroicons). 2px stroke. Black or Red.
- **Diagrams:** "Flat" style. White boxes with 2px Black borders. No drop shadows. Orthogonal lines (90-degree turns).

**Animation (CSS):**
- **Entrance:** Simple Fade-in (0.5s) or Slide-up (20px, 0.4s).
- **Stagger:** 0.1s delay for list items.
- **No Motion:** No bounces, spins, or complex paths. "Instant" feel preferred.

**Charts:**
- **Style:** 2D Flat.
- **Grid:** Horizontal only (Light Gray).
- **Data Ink:** Remove borders, backgrounds, 3D effects. Focus on the bars/lines.

---

## 4. Implementation Restrictions

**MANDATORY:**
1.  **NO Emojis:** Use generic SVG icons (database, server, code, graph).
2.  **Content Safety:** Do NOT generate real student names, university emails, or specific codebases. Use placeholders like `{{STUDENT_NAME}}`, `{{REPO_URL}}`, `{{CODE_SNIPPET}}`.
3.  **Density Control:**
    - Maximum 7 lines of body text per slide.
    - If a topic requires more explanation, generate sequential slides (e.g., `implementation_p1.html`, `implementation_p2.html`).
4.  **Visuals:**
    - No gradients.
    - No rounded corners >0px (Strict square) OR minimal 4px.
    - All layouts must respect the 120px vertical grid lines.
