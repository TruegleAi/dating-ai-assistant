# MUNCH AI - Quick Start Implementation Guide

This guide provides ready-to-use code snippets to get your Munch AI integration up and running quickly.

## Prerequisites

- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Your AI API key (DeepSeek, OpenAI, Claude, etc.)

## Quick Setup (30 minutes)

### 1. Project Initialization

```bash
# Create project directory
mkdir munch-ai-backend
cd munch-ai-backend

# Initialize npm project
npm init -y

# Install dependencies
npm install express pg ioredis jsonwebtoken bcrypt dotenv
npm install --save-dev typescript @types/express @types/node @types/pg ts-node nodemon
npm install --save-dev jest @types/jest ts-jest supertest @types/supertest

# Initialize TypeScript
npx tsc --init
```

### 2. Project Structure

```
munch-ai-backend/
├── src/
│   ├── models/
│   │   ├── ResponseType.ts
│   │   ├── ConversationStatus.ts
│   │   ├── Conversation.ts
│   │   ├── Message.ts
│   │   └── AnalysisResult.ts
│   ├── services/
│   │   ├── AnalysisService.ts
│   │   ├── ConversationService.ts
│   │   ├── ImageAnalysisService.ts
│   │   └── TrackingService.ts
│   ├── routes/
│   │   ├── conversations.ts
│   │   ├── analytics.ts
│   │   └── health.ts
│   ├── middleware/
│   │   ├── auth.ts
│   │   └── rateLimiter.ts
│   ├── database/
│   │   ├── db.ts
│   │   └── migrations/
│   └── server.ts
├── tests/
├── .env
├── .env.example
├── tsconfig.json
└── package.json
```

### 3. Environment Configuration

Create `.env` file:

```bash
# .env
NODE_ENV=development
PORT=8080

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/munch_ai

# Redis
REDIS_URL=redis://localhost:6379

# AI Service (choose one)
DEEPSEEK_API_KEY=your_deepseek_key
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key

# Authentication
JWT_SECRET=your_super_secret_jwt_key_change_in_production
JWT_EXPIRATION=7d

# File Upload
MAX_FILE_SIZE=5242880
ALLOWED_FILE_TYPES=image/jpeg,image/png,image/gif

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100
```

### 4. Database Setup

Run this SQL to initialize your database:

```sql
-- Create database
CREATE DATABASE munch_ai;

-- Connect to database
\c munch_ai

-- Create tables
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(100),
  password_hash VARCHAR(255) NOT NULL,
  subscription_tier VARCHAR(50) DEFAULT 'free',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  response_type VARCHAR(50) NOT NULL,
  chemistry_score INTEGER DEFAULT 0,
  success_rate DECIMAL(5,2) DEFAULT 0.00,
  failure_rate DECIMAL(5,2) DEFAULT 0.00,
  total_messages INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_message_at TIMESTAMP
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  image_url TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  chemistry_score INTEGER NOT NULL,
  success_rate DECIMAL(5,2) NOT NULL,
  failure_rate DECIMAL(5,2) NOT NULL,
  ai_tip TEXT,
  analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_analytics_conversation_id ON analytics(conversation_id);
```

### 5. Core Files

#### src/database/db.ts

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const query = async (text: string, params?: any[]) => {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
};

export const getClient = () => pool.connect();

export default pool;
```

#### src/models/ResponseType.ts

```typescript
export enum ResponseType {
  DATING_APP = 'Dating App',
  TEXT = 'Text',
  DMS = 'DMs',
  COLD_APPROACH = 'Cold Approach',
  LIVE_DATING = 'Live Dating',
  OPENERS = 'Openers / Closers',
  PRACTICE = 'Practice'
}
```

#### src/models/ConversationStatus.ts

```typescript
export enum ConversationStatus {
  ACTIVE = 'active',
  STALLED = 'stalled',
  GHOSTED = 'ghosted',
  SUCCESS = 'success'
}
```

#### src/models/Conversation.ts

```typescript
import { ConversationStatus } from './ConversationStatus';
import { ResponseType } from './ResponseType';

export interface Conversation {
  id: string;
  userId: string;
  name: string;
  status: ConversationStatus;
  responseType: ResponseType;
  chemistryScore: number;
  successRate: number;
  failureRate: number;
  totalMessages: number;
  createdAt: Date;
  updatedAt: Date;
  lastMessageAt?: Date;
}

export interface CreateConversationDto {
  userId: string;
  name: string;
  responseType: ResponseType;
}
```

#### src/models/Message.ts

```typescript
export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  imageUrl?: string;
  metadata?: Record<string, any>;
  createdAt: Date;
}

export interface CreateMessageDto {
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  imageUrl?: string;
  metadata?: Record<string, any>;
}
```

#### src/models/AnalysisResult.ts

```typescript
export interface AnalysisResult {
  conversationId: string;
  chemistryScore: number;
  successRate: number;
  failureRate: number;
  aiTip: string;
  analyzedAt: Date;
}
```

#### src/services/AnalysisService.ts (DeepSeek Example)

```typescript
import { Message } from '../models/Message';
import { ResponseType } from '../models/ResponseType';
import { AnalysisResult } from '../models/AnalysisResult';

export class AnalysisService {
  private apiKey: string;
  private baseUrl: string = 'https://api.deepseek.com/v1';

  constructor() {
    this.apiKey = process.env.DEEPSEEK_API_KEY || '';
    if (!this.apiKey) {
      throw new Error('DEEPSEEK_API_KEY is required');
    }
  }

  async analyzeConversation(
    messages: Message[],
    responseType: ResponseType,
    conversationId: string
  ): Promise<AnalysisResult> {
    const prompt = this.buildAnalysisPrompt(messages, responseType);

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content: 'You are a dating conversation analyst. Respond only with valid JSON.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          response_format: { type: 'json_object' },
          temperature: 0.7
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;
      const analysis = JSON.parse(content);

      return {
        conversationId,
        chemistryScore: Math.min(100, Math.max(0, analysis.chemistryScore || 50)),
        successRate: Math.min(100, Math.max(0, analysis.successRate || 25)),
        failureRate: Math.min(100, Math.max(0, analysis.failureRate || 75)),
        aiTip: analysis.aiTip || 'Keep the conversation engaging and ask open-ended questions.',
        analyzedAt: new Date()
      };
    } catch (error) {
      console.error('Analysis error:', error);
      // Return fallback analysis
      return {
        conversationId,
        chemistryScore: 50,
        successRate: 25,
        failureRate: 25,
        aiTip: 'Unable to analyze at this time. Try adding more context.',
        analyzedAt: new Date()
      };
    }
  }

  async generateResponse(
    messages: Message[],
    responseType: ResponseType
  ): Promise<string> {
    const systemPrompt = this.buildSystemPrompt(responseType);

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            { role: 'system', content: systemPrompt },
            ...messages.map(m => ({
              role: m.role,
              content: m.content
            }))
          ],
          temperature: 0.8,
          max_tokens: 200
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const data = await response.json();
      return data.choices[0].message.content;
    } catch (error) {
      console.error('Response generation error:', error);
      return "I'm having trouble generating a response right now. Please try again.";
    }
  }

  private buildAnalysisPrompt(
    messages: Message[],
    responseType: ResponseType
  ): string {
    const contextMap = {
      [ResponseType.DATING_APP]: 'dating app conversation',
      [ResponseType.TEXT]: 'text message exchange',
      [ResponseType.DMS]: 'social media DM conversation',
      [ResponseType.COLD_APPROACH]: 'cold approach interaction',
      [ResponseType.LIVE_DATING]: 'live dating scenario',
      [ResponseType.OPENERS]: 'conversation opener or closer',
      [ResponseType.PRACTICE]: 'practice conversation'
    };

    const context = contextMap[responseType];
    const conversationText = messages
      .map(m => `${m.role.toUpperCase()}: ${m.content}`)
      .join('\n');

    return `Analyze this ${context}:

${conversationText}

Provide a JSON response with:
{
  "chemistryScore": <number 0-100>,
  "successRate": <number 0-100>,
  "failureRate": <number 0-100>,
  "aiTip": "<one specific actionable tip>"
}

Consider:
- Chemistry: Connection, rapport, mutual interest
- Success: Likelihood of positive outcome (date, continued conversation)
- Failure: Risk of ghosting, fading interest
- Tip: What should the user do next to improve the conversation`;
  }

  private buildSystemPrompt(responseType: ResponseType): string {
    const prompts = {
      [ResponseType.DATING_APP]: `You are an expert dating app conversation coach. Create engaging, witty responses that:
- Show genuine interest and personality
- Ask thoughtful, open-ended questions
- Use light humor when appropriate
- Build attraction naturally
- Keep responses conversational and authentic`,

      [ResponseType.TEXT]: `You are a text messaging expert. Create responses that:
- Are concise but engaging (1-3 sentences)
- Match the energy level of the conversation
- Use appropriate emojis sparingly
- Maintain mystery and intrigue
- Don't over-invest too early`,

      [ResponseType.DMS]: `You are a social media DM specialist. Create responses that:
- Are casual and confident
- Reference their profile when relevant
- Transition smoothly from online to offline
- Stand out from generic messages
- Build rapport quickly`,

      [ResponseType.COLD_APPROACH]: `You are a cold approach expert. Create responses that:
- Are confident but respectful
- Create immediate interest
- Use situational awareness
- Transition naturally to exchange contact info
- Handle rejection gracefully`,

      [ResponseType.LIVE_DATING]: `You are a live dating coach. Suggest:
- Engaging conversation topics
- Body language cues
- Ways to build chemistry in person
- When to escalate (suggest activity change)
- How to handle awkward moments`,

      [ResponseType.OPENERS]: `You are an expert in conversation starters and closers. Create:
- Unique, memorable opening lines
- Smooth transitions to exchanging contact info
- Natural ways to suggest meeting up
- Callbacks to earlier conversation points
- Ways to leave a lasting impression`,

      [ResponseType.PRACTICE]: `You are a practice conversation partner. Help users:
- Practice realistic dating scenarios
- Get constructive feedback
- Build confidence
- Identify areas for improvement
- Develop natural conversational flow`
    };

    return prompts[responseType] || prompts[ResponseType.DATING_APP];
  }
}
```

#### src/services/ConversationService.ts

```typescript
import { query } from '../database/db';
import { Conversation, CreateConversationDto } from '../models/Conversation';
import { Message, CreateMessageDto } from '../models/Message';
import { AnalysisResult } from '../models/AnalysisResult';

export class ConversationService {
  async create(dto: CreateConversationDto): Promise<Conversation> {
    const result = await query(
      `INSERT INTO conversations (user_id, name, response_type)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [dto.userId, dto.name, dto.responseType]
    );

    return this.mapRowToConversation(result.rows[0]);
  }

  async findById(id: string): Promise<Conversation | null> {
    const result = await query(
      'SELECT * FROM conversations WHERE id = $1',
      [id]
    );

    return result.rows[0] ? this.mapRowToConversation(result.rows[0]) : null;
  }

  async findByUserId(userId: string): Promise<Conversation[]> {
    const result = await query(
      `SELECT * FROM conversations 
       WHERE user_id = $1 
       ORDER BY updated_at DESC`,
      [userId]
    );

    return result.rows.map(this.mapRowToConversation);
  }

  async update(id: string, updates: Partial<Conversation>): Promise<Conversation> {
    const fields = [];
    const values = [];
    let paramIndex = 1;

    Object.entries(updates).forEach(([key, value]) => {
      if (value !== undefined) {
        fields.push(`${this.camelToSnake(key)} = $${paramIndex}`);
        values.push(value);
        paramIndex++;
      }
    });

    values.push(id);

    const result = await query(
      `UPDATE conversations 
       SET ${fields.join(', ')}, updated_at = CURRENT_TIMESTAMP
       WHERE id = $${paramIndex}
       RETURNING *`,
      values
    );

    return this.mapRowToConversation(result.rows[0]);
  }

  async delete(id: string): Promise<void> {
    await query('DELETE FROM conversations WHERE id = $1', [id]);
  }

  async addMessage(conversationId: string, dto: Omit<CreateMessageDto, 'conversationId'>): Promise<Message> {
    const result = await query(
      `INSERT INTO messages (conversation_id, role, content, image_url, metadata)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [conversationId, dto.role, dto.content, dto.imageUrl, JSON.stringify(dto.metadata)]
    );

    // Update conversation last_message_at
    await query(
      'UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP WHERE id = $1',
      [conversationId]
    );

    return this.mapRowToMessage(result.rows[0]);
  }

  async getMessages(conversationId: string, limit: number = 50): Promise<Message[]> {
    const result = await query(
      `SELECT * FROM messages 
       WHERE conversation_id = $1 
       ORDER BY created_at ASC 
       LIMIT $2`,
      [conversationId, limit]
    );

    return result.rows.map(this.mapRowToMessage);
  }

  async saveAnalysis(conversationId: string, analysis: AnalysisResult): Promise<void> {
    await query(
      `INSERT INTO analytics (conversation_id, chemistry_score, success_rate, failure_rate, ai_tip)
       VALUES ($1, $2, $3, $4, $5)`,
      [conversationId, analysis.chemistryScore, analysis.successRate, analysis.failureRate, analysis.aiTip]
    );
  }

  private mapRowToConversation(row: any): Conversation {
    return {
      id: row.id,
      userId: row.user_id,
      name: row.name,
      status: row.status,
      responseType: row.response_type,
      chemistryScore: row.chemistry_score,
      successRate: parseFloat(row.success_rate),
      failureRate: parseFloat(row.failure_rate),
      totalMessages: row.total_messages,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      lastMessageAt: row.last_message_at
    };
  }

  private mapRowToMessage(row: any): Message {
    return {
      id: row.id,
      conversationId: row.conversation_id,
      role: row.role,
      content: row.content,
      imageUrl: row.image_url,
      metadata: row.metadata,
      createdAt: row.created_at
    };
  }

  private camelToSnake(str: string): string {
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
  }
}
```

#### src/routes/conversations.ts

```typescript
import express from 'express';
import { ConversationService } from '../services/ConversationService';
import { AnalysisService } from '../services/AnalysisService';
import { authenticate } from '../middleware/auth';

const router = express.Router();
const conversationService = new ConversationService();
const analysisService = new AnalysisService();

// All routes require authentication
router.use(authenticate);

// POST /api/conversations
router.post('/', async (req, res) => {
  try {
    const { name, responseType } = req.body;
    
    if (!name || !responseType) {
      return res.status(400).json({ error: 'Name and responseType are required' });
    }

    const conversation = await conversationService.create({
      userId: req.user!.id,
      name,
      responseType
    });

    res.status(201).json(conversation);
  } catch (error: any) {
    console.error('Create conversation error:', error);
    res.status(500).json({ error: 'Failed to create conversation' });
  }
});

// GET /api/conversations
router.get('/', async (req, res) => {
  try {
    const conversations = await conversationService.findByUserId(req.user!.id);
    res.json(conversations);
  } catch (error: any) {
    console.error('Get conversations error:', error);
    res.status(500).json({ error: 'Failed to fetch conversations' });
  }
});

// GET /api/conversations/:id
router.get('/:id', async (req, res) => {
  try {
    const conversation = await conversationService.findById(req.params.id);
    
    if (!conversation) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    if (conversation.userId !== req.user!.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json(conversation);
  } catch (error: any) {
    console.error('Get conversation error:', error);
    res.status(500).json({ error: 'Failed to fetch conversation' });
  }
});

// GET /api/conversations/:id/messages
router.get('/:id/messages', async (req, res) => {
  try {
    const conversation = await conversationService.findById(req.params.id);
    
    if (!conversation) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    if (conversation.userId !== req.user!.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    const messages = await conversationService.getMessages(req.params.id);
    res.json(messages);
  } catch (error: any) {
    console.error('Get messages error:', error);
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
});

// POST /api/conversations/:id/messages
router.post('/:id/messages', async (req, res) => {
  try {
    const { content, imageUrl } = req.body;
    const conversationId = req.params.id;

    if (!content) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const conversation = await conversationService.findById(conversationId);
    
    if (!conversation) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    if (conversation.userId !== req.user!.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    // Add user message
    const userMessage = await conversationService.addMessage(conversationId, {
      role: 'user',
      content,
      imageUrl
    });

    // Get all messages for context
    const messages = await conversationService.getMessages(conversationId);

    // Generate AI response
    const aiResponse = await analysisService.generateResponse(
      messages,
      conversation.responseType
    );

    // Add AI message
    const assistantMessage = await conversationService.addMessage(conversationId, {
      role: 'assistant',
      content: aiResponse
    });

    res.json({
      userMessage,
      assistantMessage
    });
  } catch (error: any) {
    console.error('Add message error:', error);
    res.status(500).json({ error: 'Failed to add message' });
  }
});

// POST /api/conversations/:id/analyze
router.post('/:id/analyze', async (req, res) => {
  try {
    const conversationId = req.params.id;
    const conversation = await conversationService.findById(conversationId);
    
    if (!conversation) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    if (conversation.userId !== req.user!.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    const messages = await conversationService.getMessages(conversationId);

    if (messages.length === 0) {
      return res.status(400).json({ error: 'No messages to analyze' });
    }

    const analysis = await analysisService.analyzeConversation(
      messages,
      conversation.responseType,
      conversationId
    );

    // Update conversation with analysis results
    await conversationService.update(conversationId, {
      chemistryScore: analysis.chemistryScore,
      successRate: analysis.successRate,
      failureRate: analysis.failureRate
    });

    // Save analysis to history
    await conversationService.saveAnalysis(conversationId, analysis);

    res.json(analysis);
  } catch (error: any) {
    console.error('Analyze conversation error:', error);
    res.status(500).json({ error: 'Failed to analyze conversation' });
  }
});

// DELETE /api/conversations/:id
router.delete('/:id', async (req, res) => {
  try {
    const conversation = await conversationService.findById(req.params.id);
    
    if (!conversation) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    if (conversation.userId !== req.user!.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    await conversationService.delete(req.params.id);
    res.status(204).send();
  } catch (error: any) {
    console.error('Delete conversation error:', error);
    res.status(500).json({ error: 'Failed to delete conversation' });
  }
});

export default router;
```

#### src/middleware/auth.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

interface JwtPayload {
  id: string;
  email: string;
}

declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

export function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as JwtPayload;
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}
```

#### src/server.ts

```typescript
import express from 'express';
import dotenv from 'dotenv';
import conversationsRouter from './routes/conversations';

dotenv.config();

const app = express();
const port = process.env.PORT || 8080;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/conversations', conversationsRouter);

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.listen(port, () => {
  console.log(`🚀 Munch AI Backend running on port ${port}`);
  console.log(`📊 Health check: http://localhost:${port}/health`);
});
```

### 6. Running the Application

```bash
# Development mode with auto-reload
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run tests
npm test
```

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

### 7. Testing the API

```bash
# Create a conversation
curl -X POST http://localhost:8080/api/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Test Conversation",
    "responseType": "Dating App"
  }'

# Add a message
curl -X POST http://localhost:8080/api/conversations/:id/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "content": "Hey! How are you doing?"
  }'

# Analyze conversation
curl -X POST http://localhost:8080/api/conversations/:id/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get all conversations
curl http://localhost:8080/api/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Next Steps

1. **Add User Authentication**: Implement user registration and login endpoints
2. **Add Image Upload**: Integrate S3 or similar for screenshot uploads
3. **Add WebSocket Support**: For real-time updates
4. **Add Analytics Endpoints**: Implement the analytics routes from the main action plan
5. **Add Rate Limiting**: Implement the rate limiting middleware
6. **Add Tests**: Write unit and integration tests
7. **Deploy**: Follow Phase 6 of the main action plan for deployment

## Common Issues & Solutions

**Issue: Database connection fails**
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running: `sudo service postgresql status`
- Verify database exists: `psql -l`

**Issue: AI API calls fail**
- Verify API key is set correctly
- Check API endpoint URL
- Monitor rate limits

**Issue: TypeScript compilation errors**
- Run `npm install` again
- Check tsconfig.json settings
- Ensure all @types packages are installed

## Resources

- [Main Action Plan](./Munch_AI_Integration_Action_Plan.md)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Express.js Guide](https://expressjs.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)

---

Ready to build? Start with the project initialization and work through each section. The complete backend will be functional after completing all steps!
