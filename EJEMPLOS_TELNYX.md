# Ruta de informacion
```
https://developers.telnyx.com/docs/messaging/messages/receive-message
```

#Send a message from your Telnyx number

```
curl -X POST \
  --header "Content-Type: application/json" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer <YOUR_API_KEY>" \
  --data '{
    "from": "+18182442184",
    "to": "+19512131452",
    "text": "Order a large pizza and get 1 FREE appetizer using the code PIZZA-FRIDAY. Order now: http://random-url-7o6sqs.com/

Reply STOP to opt-out of text messages",
    "media_urls" : []
  }' \
  https://api.telnyx.com/v2/messages
```

Raw Response 

```json
{
  "data": {
    "record_type": "message",
    "direction": "outbound",
    "id": "40319665-268f-4395-8954-f8b09f99dee2",
    "type": "SMS",
    "organization_id": "292dd3be-6fc8-42b4-b08f-b1b9cd78d296",
    "messaging_profile_id": "40019664-b1b0-4e53-b383-05c32381d135",
    "from": {
      "phone_number": "+18182442184",
      "carrier": "Telnyx",
      "line_type": "Wireless"
    },
    "to": [
      {
        "phone_number": "+19512131452",
        "status": "queued",
        "carrier": "T-MOBILE USA, INC.",
        "line_type": "Wireless"
      }
    ],
    "cc": [],
    "text": "Order a large pizza and get 1 FREE appetizer using the code PIZZA-FRIDAY. Order now: http://random-url-7o6sqs.com/\n\nReply STOP to opt-out of text messages",
    "media": [],
    "webhook_url": "http://mensajes.paseotravel.com/webhook/sms",
    "webhook_failover_url": "",
    "encoding": "GSM-7",
    "parts": 1,
    "tags": [
      "SimpleOrthotics"
    ],
    "cost": {
      "amount": "0.0160",
      "currency": "USD"
    },
    "tcr_campaign_id": null,
    "tcr_campaign_billable": false,
    "tcr_campaign_registered": null,
    "received_at": "2025-04-24T00:15:48.076+00:00",
    "sent_at": null,
    "completed_at": null,
    "valid_until": "2025-04-24T01:15:48.076+00:00",
    "errors": [],
    "cost_breakdown": {
      "rate": {
        "amount": "0.00400",
        "currency": "USD"
      },
      "carrier_fee": {
        "amount": "0.01200",
        "currency": "USD"
      }
    }
  }
}
```

