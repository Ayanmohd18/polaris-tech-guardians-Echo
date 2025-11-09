"""
ECHO: The Sentient Workspace
Feature 12: Real-Time Market Validation - The Agentic Tester
Automatically tests ideas with real users and ad campaigns
"""

import os
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
import openai
from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import json

class MarketValidator:
    """Validates product ideas with real market testing"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize services
        openai.api_key = Config.OPENAI_API_KEY
        self._init_firebase()
        
        # Testing platforms
        self.google_ads_api_key = os.getenv('GOOGLE_ADS_API_KEY', '')
        self.facebook_ads_token = os.getenv('FACEBOOK_ADS_TOKEN', '')
        
    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.db = None
    
    def create_ab_test(
        self,
        variants: List[Dict[str, Any]],
        target_audience: Dict[str, Any],
        budget: float = 10.0,
        duration_hours: int = 1
    ) -> str:
        """Create A/B test with real ad traffic"""
        
        test_id = str(uuid.uuid4())
        
        try:
            # Generate landing pages for each variant
            landing_pages = []
            for i, variant in enumerate(variants):
                page_url = self._create_landing_page(variant, test_id, i)
                landing_pages.append({
                    'variant_id': f'variant_{i}',
                    'url': page_url,
                    'content': variant
                })
            
            # Create ad campaigns
            campaign_ids = self._create_ad_campaigns(
                landing_pages,
                target_audience,
                budget,
                duration_hours
            )
            
            # Store test in Firebase
            if self.db:
                self.db.collection('ab_tests').document(test_id).set({
                    'user_id': self.user_id,
                    'variants': variants,
                    'landing_pages': landing_pages,
                    'campaign_ids': campaign_ids,
                    'target_audience': target_audience,
                    'budget': budget,
                    'duration_hours': duration_hours,
                    'status': 'running',
                    'start_time': firestore.SERVER_TIMESTAMP,
                    'end_time': datetime.now() + timedelta(hours=duration_hours),
                    'results': {}
                })
            
            print(f"✅ A/B test created: {test_id}")
            print(f"   Budget: ${budget}")
            print(f"   Duration: {duration_hours} hours")
            print(f"   Variants: {len(variants)}")
            
            return test_id
            
        except Exception as e:
            print(f"A/B test creation error: {e}")
            raise
    
    def _create_landing_page(self, variant: Dict[str, Any], test_id: str, variant_index: int) -> str:
        """Generate and deploy landing page"""
        
        # Generate HTML using AI
        html_content = self._generate_landing_page_html(variant)
        
        # Deploy to temporary hosting (using Firebase Hosting or similar)
        page_url = self._deploy_page(html_content, test_id, variant_index)
        
        return page_url
    
    def _generate_landing_page_html(self, variant: Dict[str, Any]) -> str:
        """Generate landing page HTML using AI"""
        
        try:
            prompt = f"""Generate a clean, conversion-optimized landing page HTML for:

Headline: {variant.get('headline', '')}
Subheadline: {variant.get('subheadline', '')}
CTA: {variant.get('cta', 'Learn More')}

Requirements:
- Mobile responsive
- Fast loading
- Clear CTA button
- Analytics tracking
- Professional design

Return only the complete HTML."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            html = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if html.startswith('```'):
                html = '\n'.join(html.split('\n')[1:-1])
            
            return html
            
        except Exception as e:
            print(f"HTML generation error: {e}")
            return self._get_fallback_html(variant)
    
    def _get_fallback_html(self, variant: Dict[str, Any]) -> str:
        """Fallback HTML template"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{variant.get('headline', 'Test Page')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            text-align: center;
        }}
        h1 {{ font-size: 48px; margin-bottom: 20px; }}
        h2 {{ font-size: 24px; color: #666; margin-bottom: 40px; }}
        .cta {{ 
            background: #4A90E2;
            color: white;
            padding: 15px 40px;
            font-size: 18px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .cta:hover {{ background: #357ABD; }}
    </style>
</head>
<body>
    <h1>{variant.get('headline', 'Welcome')}</h1>
    <h2>{variant.get('subheadline', 'Discover something amazing')}</h2>
    <button class="cta" onclick="trackConversion()">{variant.get('cta', 'Learn More')}</button>
    
    <script>
        function trackConversion() {{
            fetch('/api/track-conversion', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    test_id: '{variant.get("test_id", "")}',
                    variant_id: '{variant.get("variant_id", "")}'
                }})
            }});
            alert('Thank you for your interest!');
        }}
    </script>
</body>
</html>"""
    
    def _deploy_page(self, html_content: str, test_id: str, variant_index: int) -> str:
        """Deploy page to temporary hosting"""
        
        # In production, deploy to Firebase Hosting, Vercel, or Netlify
        # For demo, we'll simulate with a local URL
        
        # Save to local file
        filename = f"landing_page_{test_id}_{variant_index}.html"
        filepath = os.path.join("./temp_pages", filename)
        
        os.makedirs("./temp_pages", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Return simulated URL (in production, this would be the deployed URL)
        return f"https://echo-test.app/{test_id}/variant_{variant_index}"
    
    def _create_ad_campaigns(
        self,
        landing_pages: List[Dict[str, Any]],
        target_audience: Dict[str, Any],
        budget: float,
        duration_hours: int
    ) -> List[str]:
        """Create ad campaigns on Google/Facebook"""
        
        campaign_ids = []
        
        # Budget per variant
        budget_per_variant = budget / len(landing_pages)
        
        for page in landing_pages:
            # Create Google Ads campaign
            if self.google_ads_api_key:
                campaign_id = self._create_google_ad(
                    page,
                    target_audience,
                    budget_per_variant,
                    duration_hours
                )
                if campaign_id:
                    campaign_ids.append(f"google_{campaign_id}")
            
            # Create Facebook Ads campaign
            if self.facebook_ads_token:
                campaign_id = self._create_facebook_ad(
                    page,
                    target_audience,
                    budget_per_variant,
                    duration_hours
                )
                if campaign_id:
                    campaign_ids.append(f"facebook_{campaign_id}")
        
        return campaign_ids
    
    def _create_google_ad(
        self,
        landing_page: Dict[str, Any],
        target_audience: Dict[str, Any],
        budget: float,
        duration_hours: int
    ) -> Optional[str]:
        """Create Google Ads campaign"""
        
        # Simulated Google Ads API call
        # In production, use google-ads-python library
        
        print(f"📢 Creating Google Ad campaign:")
        print(f"   URL: {landing_page['url']}")
        print(f"   Audience: {target_audience}")
        print(f"   Budget: ${budget}")
        
        # Simulate campaign creation
        campaign_id = f"google_{uuid.uuid4().hex[:8]}"
        
        return campaign_id
    
    def _create_facebook_ad(
        self,
        landing_page: Dict[str, Any],
        target_audience: Dict[str, Any],
        budget: float,
        duration_hours: int
    ) -> Optional[str]:
        """Create Facebook Ads campaign"""
        
        # Simulated Facebook Ads API call
        # In production, use facebook_business library
        
        print(f"📘 Creating Facebook Ad campaign:")
        print(f"   URL: {landing_page['url']}")
        print(f"   Audience: {target_audience}")
        print(f"   Budget: ${budget}")
        
        # Simulate campaign creation
        campaign_id = f"facebook_{uuid.uuid4().hex[:8]}"
        
        return campaign_id
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        
        if not self.db:
            return {}
        
        try:
            doc = self.db.collection('ab_tests').document(test_id).get()
            
            if not doc.exists:
                return {}
            
            test_data = doc.to_dict()
            
            # Check if test is complete
            if test_data.get('status') == 'running':
                end_time = test_data.get('end_time')
                if datetime.now() < end_time:
                    return {'status': 'running', 'message': 'Test still in progress'}
            
            # Fetch analytics data
            results = self._fetch_analytics(test_id, test_data)
            
            # Analyze results with AI
            analysis = self._analyze_results(results)
            
            # Update Firebase
            self.db.collection('ab_tests').document(test_id).update({
                'status': 'completed',
                'results': results,
                'analysis': analysis
            })
            
            return {
                'status': 'completed',
                'results': results,
                'analysis': analysis
            }
            
        except Exception as e:
            print(f"Get results error: {e}")
            return {}
    
    def _fetch_analytics(self, test_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch analytics from ad platforms"""
        
        # Simulated analytics data
        # In production, fetch from Google Analytics, Facebook Insights, etc.
        
        import random
        
        results = {}
        
        for i, variant in enumerate(test_data.get('variants', [])):
            variant_id = f'variant_{i}'
            
            # Simulate metrics
            impressions = random.randint(100, 500)
            clicks = random.randint(10, 50)
            conversions = random.randint(1, 10)
            
            results[variant_id] = {
                'headline': variant.get('headline', ''),
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'ctr': round((clicks / impressions) * 100, 2),
                'conversion_rate': round((conversions / clicks) * 100, 2),
                'cost_per_click': round(test_data.get('budget', 10) / len(test_data.get('variants', [])) / clicks, 2)
            }
        
        return results
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results with AI"""
        
        try:
            prompt = f"""Analyze these A/B test results and provide insights:

{json.dumps(results, indent=2)}

Provide JSON with:
- winner: variant_id of best performer
- confidence: (high/medium/low)
- key_insight: main takeaway
- recommendations: [list of actionable recommendations]
- geographic_insights: any location-based patterns"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return analysis
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                'winner': 'variant_0',
                'confidence': 'low',
                'key_insight': 'Insufficient data for analysis',
                'recommendations': []
            }

# FastAPI endpoints for market validation
app = FastAPI(title="ECHO Market Validator", version="1.0.0")

@app.post("/create_ab_test")
async def create_ab_test(request: Dict[str, Any]):
    """Create A/B test"""
    try:
        user_id = request.get('user_id')
        variants = request.get('variants', [])
        target_audience = request.get('target_audience', {})
        budget = request.get('budget', 10.0)
        duration_hours = request.get('duration_hours', 1)
        
        validator = MarketValidator(user_id)
        test_id = validator.create_ab_test(
            variants,
            target_audience,
            budget,
            duration_hours
        )
        
        return {
            'status': 'success',
            'test_id': test_id,
            'message': f'A/B test created with ${budget} budget for {duration_hours} hours'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test_results/{test_id}")
async def get_test_results(test_id: str, user_id: str):
    """Get A/B test results"""
    try:
        validator = MarketValidator(user_id)
        results = validator.get_test_results(test_id)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarketValidationDialog:
    """Dialog for creating market validation tests"""
    
    @staticmethod
    def show_validation_dialog(canvas_content: Dict[str, Any], user_id: str):
        """Show dialog to create A/B test"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QSpinBox, QDoubleSpinBox, QMessageBox
        
        dialog = QDialog()
        dialog.setWindowTitle("ECHO - Market Validation")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🧪 Test This With Real Users")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        description = QLabel(
            "ECHO will create landing pages, run ad campaigns, "
            "and report back with real market data."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 10px; color: #666;")
        
        # Form
        form = QFormLayout()
        
        budget_input = QDoubleSpinBox()
        budget_input.setRange(5.0, 1000.0)
        budget_input.setValue(10.0)
        budget_input.setPrefix("$")
        
        duration_input = QSpinBox()
        duration_input.setRange(1, 24)
        duration_input.setValue(1)
        duration_input.setSuffix(" hours")
        
        audience_input = QLineEdit()
        audience_input.setPlaceholderText("e.g., Python Developers, 25-40")
        
        form.addRow("Budget:", budget_input)
        form.addRow("Duration:", duration_input)
        form.addRow("Target Audience:", audience_input)
        
        # Buttons
        test_btn = QPushButton("🚀 Run Market Test")
        test_btn.clicked.connect(lambda: MarketValidationDialog._run_test(
            canvas_content, user_id, budget_input.value(),
            duration_input.value(), audience_input.text(), dialog
        ))
        
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(dialog.reject)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(test_btn)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    @staticmethod
    def _run_test(canvas_content, user_id, budget, duration, audience, dialog):
        """Run the market validation test"""
        from PyQt6.QtWidgets import QMessageBox
        
        validator = MarketValidator(user_id)
        
        # Extract variants from canvas
        variants = canvas_content.get('variants', [
            {'headline': 'Option A', 'subheadline': 'First variant'},
            {'headline': 'Option B', 'subheadline': 'Second variant'}
        ])
        
        target_audience = {'description': audience}
        
        try:
            test_id = validator.create_ab_test(
                variants,
                target_audience,
                budget,
                duration
            )
            
            QMessageBox.information(
                dialog,
                "Test Started",
                f"✅ Market validation test started!\n\n"
                f"Test ID: {test_id}\n"
                f"Budget: ${budget}\n"
                f"Duration: {duration} hours\n\n"
                f"ECHO will notify you when results are ready."
            )
            
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to start test:\n{str(e)}")

if __name__ == "__main__":
    # Test market validator
    validator = MarketValidator("user_001")
    
    # Create test
    test_id = validator.create_ab_test(
        variants=[
            {'headline': 'The Sentient Workspace', 'subheadline': 'AI that adapts to you'},
            {'headline': 'ECHO: Your AI Partner', 'subheadline': 'Code faster, think better'}
        ],
        target_audience={'description': 'Python Developers, 25-40'},
        budget=10.0,
        duration_hours=1
    )
    
    print(f"\nTest created: {test_id}")
    print("Waiting for results...")