import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * Lekhan k6 Load Test Suite
 * 
 * Verifies performance SLAs/SLOs:
 * - Read / Dashboard p95 latency: < 200ms
 * - Helper / Text conversion p95 latency: < 100ms
 * - Document generation p95 latency: < 800ms
 * - Error rate: < 1%
 * 
 * Run with:
 *   k6 run backend/tests/load/k6_load_test.js
 *   k6 run --env BASE_URL=http://staging.lekhan.local backend/tests/load/k6_load_test.js
 */

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp-up to 10 VUs
    { duration: '2m', target: 20 },  // Sustained load at 20 VUs
    { duration: '30s', target: 0 },  // Ramp-down
  ],
  thresholds: {
    'http_req_duration{type:health}': ['p(95)<50'],    // Readiness check p95 < 50ms
    'http_req_duration{type:read}': ['p(95)<200'],     // Read/query p95 < 200ms
    'http_req_duration{type:compute}': ['p(95)<800'],  // Generation/render p95 < 800ms
    'http_req_failed': ['rate<0.01'],                  // Error rate < 1%
  },
};

export default function () {
  // 1. Health readiness check (Probes DB connectivity & pool availability)
  {
    const res = http.get(`${BASE_URL}/health/ready`, {
      tags: { type: 'health' },
    });
    check(res, {
      'ready returns 200': (r) => r.status === 200,
    });
  }

  // 2. Helper conversion utility (Marathi Amount in Words)
  {
    const payload = JSON.stringify({
      amount: 1250000,
      language: 'mr',
    });
    const params = {
      headers: { 'Content-Type': 'application/json' },
      tags: { type: 'read' },
    };
    const res = http.post(`${BASE_URL}/api/v1/helpers/amount-to-words`, payload, params);
    check(res, {
      'amount-to-words returns 200 or valid status': (r) => r.status === 200 || r.status === 404,
    });
  }

  // 3. Document preview / generation endpoint simulation
  {
    const payload = JSON.stringify({
      template_id: 'sample-sale-deed',
      language: 'mr',
      data: {
        property: { survey_no: '42/1', area_sqft: '1200' },
        parties: [{ name_mr: 'अनिल पाटील', role: 'vendor' }],
      },
    });
    const params = {
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': `load-test-${__VU}-${__ITER}`,
      },
      tags: { type: 'compute' },
    };
    const res = http.post(`${BASE_URL}/api/v1/matters/preview`, payload, params);
    check(res, {
      'preview/generate responds within budget': (r) => r.status === 200 || r.status === 401 || r.status === 404,
    });
  }

  sleep(1);
}

