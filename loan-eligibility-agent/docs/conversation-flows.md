# Conversation Flow Design

## Overview

The Loan Eligibility Agent uses a state-machine based conversation flow to guide users through the pre-qualification process. This document details the conversation design, intent handling, and flow transitions.

## Flow Diagram

```
                         ┌─────────────┐
                         │   START     │
                         └──────┬──────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                        WELCOME                                │
│  "What type of loan are you interested in?"                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Personal │    │   Home   │    │   Auto   │  ... etc
    └────┬─────┘    └────┬─────┘    └────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   COLLECT LOAN AMOUNT                         │
│  "How much would you like to borrow?"                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   COLLECT INCOME                              │
│  "What is your approximate annual income?"                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   COLLECT EMPLOYMENT                          │
│  "What is your current employment status?"                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   COLLECT CREDIT SCORE                        │
│  "Do you know your approximate credit score?"                │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   COLLECT DEBT                                │
│  "What is your approximate total existing debt?"             │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   CONFIRM DETAILS                             │
│  "Is this information correct?"                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
         ┌────────┐              ┌────────────┐
         │  YES   │              │     NO     │
         └───┬────┘              └─────┬──────┘
             │                         │
             │                    ┌────┴────┐
             │                    │CORRECTION│
             │                    │ HANDLER  │
             │                    └────┬────┘
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   CHECK ELIGIBILITY                           │
│  [Backend processing]                                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌────────────┐    ┌────────────────┐    ┌────────────┐
│  ELIGIBLE  │    │ CONDITIONALLY  │    │    NOT     │
│            │    │   ELIGIBLE     │    │  ELIGIBLE  │
└─────┬──────┘    └───────┬────────┘    └─────┬──────┘
      │                   │                   │
      ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                   NEXT STEPS / HANDOFF                        │
└──────────────────────────────────────────────────────────────┘
```

## Conversation Steps

### 1. Welcome

**Purpose**: Greet user and present loan options

**Entry Message**:
```
Welcome to our loan pre-qualification service! I'm here to help you
understand your loan options.

I can help you check your eligibility for:
• Personal loans
• Home loans
• Auto loans
• Business loans
• Education loans

What type of loan are you interested in today?
```

**Expected Intents**:
- `loan.type.personal`
- `loan.type.home`
- `loan.type.auto`
- `loan.type.business`
- `loan.type.education`
- `request.human.agent`

---

### 2. Collect Loan Amount

**Purpose**: Gather requested loan amount

**Entry Message**:
```
Great choice! How much would you like to borrow?
```

**Validation**:
- Must be positive number
- Must be within loan type limits
- Webhook tag: `validate_loan_amount`

**Expected Entities**:
- `@sys.unit-currency`

---

### 3. Collect Income

**Purpose**: Gather annual income

**Entry Message**:
```
Now, let's look at your financial situation.
What is your approximate annual income before taxes?
```

**Validation**:
- Must be positive number
- Affordability warning if loan-to-income > 5x
- Webhook tag: `validate_income`

---

### 4. Collect Employment

**Purpose**: Determine employment stability

**Entry Message**:
```
What is your current employment status?

• Employed (full-time or part-time)
• Self-employed
• Retired
• Student
• Currently not employed
```

**Expected Entities**:
- `@employment_status` (custom entity)

---

### 5. Collect Credit Score

**Purpose**: Assess creditworthiness

**Entry Message**:
```
Do you know your approximate credit score?

If you're not sure, that's okay - you can say "I don't know."
Credit scores typically range from 300 to 850.

Common ranges:
• Excellent: 750+
• Good: 700-749
• Fair: 650-699
• Needs improvement: Below 650
```

**Handling Unknown**:
- Intent: `credit.score.unknown`
- Default estimate: 650
- Webhook tag: `validate_credit_score`

---

### 6. Collect Debt

**Purpose**: Calculate debt-to-income ratio

**Entry Message**:
```
Almost done! What is your approximate total existing debt?

This includes:
• Credit card balances
• Car loans
• Student loans
• Other loans

An estimate is fine, or say "none" if you have no debt.
```

**Expected Intents**:
- `debt.none` → Sets debt to 0
- Numeric value via `@sys.unit-currency`

---

### 7. Confirm Details

**Purpose**: Verify collected information before assessment

**Entry Message**:
```
Thank you for providing that information. Let me confirm:

**Loan Request:**
• Type: {loan_type}
• Amount: ${loan_amount}

**Your Financial Profile:**
• Annual Income: ${annual_income}
• Employment: {employment_status}
• Credit Score: {credit_score}
• Existing Debt: ${existing_debt}

Is this information correct?
```

**Expected Intents**:
- `confirmation.yes` → Proceed to eligibility check
- `confirmation.no` → Correction handler

---

### 8. Check Eligibility

**Purpose**: Run eligibility assessment

**Processing**:
1. Call `check_eligibility` webhook
2. Evaluate all factors
3. Generate LLM explanation
4. Route to appropriate result page

---

### 9. Result Pages

#### Eligible Result
```
🎉 Great news!

Based on your information, you pre-qualify for a {loan_type} loan!

**Your Pre-Approved Offer:**
• Amount: Up to ${approved_amount}
• Estimated Rate: {rate}%
• Estimated Monthly Payment: ${monthly_payment}

**Next Steps:**
1. Complete the full application
2. Gather required documentation
3. Schedule an appointment with a loan officer

Would you like to proceed with the full application?
```

#### Conditionally Eligible Result
```
Good news! You may qualify for a {loan_type} loan with some conditions.

We could potentially approve ${approved_amount}.

Some factors require additional review:
{factor_list}

Would you like to discuss your options with a loan specialist?
```

#### Not Eligible Result
```
Thank you for your interest in our loan products.

Based on our current lending criteria, we're unable to pre-qualify
you for this loan at this time.

**Factors that may have affected this decision:**
{factor_list}

**What you can do:**
1. Review and improve factors affecting eligibility
2. Consider a co-signer
3. Explore alternative options
4. Speak with a loan specialist

Would you like to learn more about improving your eligibility?
```

---

## Intent Handling

### Primary Intents

| Intent | Training Phrases | Action |
|--------|-----------------|--------|
| `loan.type.personal` | "personal loan", "I need a personal loan" | Set loan_type = personal |
| `loan.type.home` | "mortgage", "home loan", "buy a house" | Set loan_type = home |
| `confirmation.yes` | "yes", "correct", "that's right" | Proceed |
| `confirmation.no` | "no", "wrong", "incorrect" | Correction flow |
| `request.human.agent` | "talk to human", "speak to someone" | Human handoff |
| `credit.score.unknown` | "I don't know", "not sure" | Use estimate |
| `debt.none` | "none", "no debt", "zero" | Set debt = 0 |

### Fallback Handling

```
I didn't quite catch that. Could you please rephrase?

If you're having trouble, you can say:
• "Help" for assistance
• "Start over" to restart
• "Talk to someone" for human help
```

---

## Error Recovery

### No Match (3 times)
```
I'm having trouble understanding. Let me connect you with a
specialist who can help. One moment please...
```

### No Input (2 times)
```
Are you still there? I'm here to help with your loan
pre-qualification. Would you like to continue?
```

### Validation Error
```
I need a valid {field_name}. For example, you can say
'{example_value}'. Would you like to try again?
```

---

## Context Management

### Session Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `loan_type` | string | Selected loan type |
| `loan_amount` | number | Requested amount |
| `annual_income` | number | Annual income |
| `employment_status` | string | Employment status |
| `credit_score` | number | Credit score (or estimate) |
| `existing_debt` | number | Total existing debt |
| `eligibility_status` | string | Result of assessment |
| `approved_amount` | number | Approved loan amount |
| `estimated_rate` | number | Interest rate estimate |

### Context Lifespan

- `loan-application`: 50 turns (main context)
- `awaiting-confirmation`: 2 turns
- `correction-mode`: 5 turns
- `eligibility-result`: 10 turns

---

## Compliance Integration

### Automatic Disclaimers

Disclaimers are automatically appended at key points:

1. **After eligibility result**:
   > *This is a pre-qualification estimate and not a final loan offer.*

2. **With rate quotes**:
   > *Interest rates shown are estimates and may vary.*

3. **Privacy notice** (at confirmation):
   > *Your information is protected and will only be used for
   > loan pre-qualification purposes.*

### Audit Logging

All conversation events are logged:
- Intent detections
- Parameter updates
- Eligibility decisions
- Human handoff requests
- Error conditions
