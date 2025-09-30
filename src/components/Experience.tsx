import { Card } from "@/components/ui/card";
import deloitteLogo from "@/assets/deloitte-logo.jpg";
import featuredLogo from "@/assets/featured.jpg";
import uaLogo from "@/assets/university-arizona.jpg";
import nagpurLogo from "@/assets/nagpur-university.png";
import alteryxLogo from "@/assets/alteryx-logo.jpg";
import databricksLogo from "@/assets/databricks.png";

export const Experience = () => {
  const experiences = [
    {
      company: "Featured (Terkel Inc.)",
      logo: featuredLogo,
      role: "Software Engineer Intern – Data Science",
      period: "July 2025 – September 2025",
      location: "Scottsdale, Arizona",
      highlights: [
        "Implemented a content-based recommendation engine to rank expert profiles against news articles, utilizing text embeddings and cosine similarity to enhance the accuracy of expert matching.",
        "Developed a Slack integration that pushed curated opportunities directly to user workspaces 3x daily, creating a new, high-engagement distribution channel for the platform.",
        "Partnered with cross-functional engineering and product teams on key initiatives, contributing directly to the improvement of the platform's data infrastructure and third-party API connectivity."
      ],
      type: "experience"
    },
    {
      company: "University of Arizona",
      logo: uaLogo,
      role: "Student Worker, Planning & Operations",
      period: "October 2024 – May 2025",
      location: "Phoenix, Arizona",
      highlights: [
        "Engineered a comprehensive KPI framework supported by an advanced data warehouse, yielding critical insights that drove a 15% reduction in excess inventory and enhanced supply chain efficiency.",
        "Established a robust data quality and governance framework using advanced statistical modeling and anomaly detection, ensuring high-fidelity reporting for strategic planning.",
        "Translated complex operational datasets into clear, actionable insights, serving as a trusted advisor to leadership and guiding high-priority operational improvement initiatives."
      ],
      type: "experience"
    },
    {
      company: "Deloitte Consulting",
      logo: deloitteLogo,
      role: "Analyst, AI & Data Engineering Practice",
      period: "January 2021 – August 2024",
      location: "Hyderabad, India",
      highlights: [
        "Guided Fortune 100 executives in architecting data modernization strategies, driving the enterprise adoption of Azure Databricks for critical systems.",
        "Designed, Developed and Deployed real-time data pipelines integrating Oracle, SAP, and payment APIs (stripe), that boosted insights into cashflow and powered advanced executive reporting in Power BI.",
        "Spearheaded the replacement of legacy ETL with modern Spark architecture, leading complex data cloud migrations using AWS services (Databricks, S3, Airflow) to cut report latency by 40%.",
        "Partnered with Product, Risk, and Finance leaders to define operational KPIs and embed analytics into workflows, leveraging a 99.9% uptime."
      ],
      type: "experience"
    }
  ];

  const education = [
    {
      institution: "University of Arizona, Eller College of Management",
      logo: uaLogo,
      degree: "Master of Science in Business Analytics",
      details: "Dean's List | GPA: 3.85/4.00",
      period: "May 2025",
      location: "Chandler, Arizona",
      type: "education"
    },
    {
      institution: "Rashtrasant Tukdoji Maharaj Nagpur University",
      logo: nagpurLogo,
      degree: "Bachelor of Computer Application",
      period: "November 2020",
      location: "Nagpur, India",
      type: "education"
    }
  ];

  const certifications = [
    {
      name: "Databricks Data Engineer Associate",
      logo: databricksLogo,
      issuer: "Databricks"
    },
    {
      name: "Alteryx Designer Core",
      logo: alteryxLogo,
      issuer: "Alteryx"
    }
  ];

  return (
    <section id="experience" className="py-20 px-4 bg-muted/20">
      <div className="container mx-auto max-w-6xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          Experience & Education
        </h2>

        <div className="space-y-12">
          {/* Experience */}
          <div>
            <h3 className="text-2xl font-semibold mb-6 text-primary">
              Professional Experience
            </h3>
            <div className="space-y-6">
              {experiences.map((exp) => (
                <Card 
                  key={exp.company}
                  className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <img 
                      src={exp.logo} 
                      alt={exp.company}
                      className="h-16 w-16 object-contain bg-white p-2 rounded flex-shrink-0"
                    />
                    <div className="flex-1">
                      <h4 className="text-xl font-semibold text-foreground">
                        {exp.company}
                      </h4>
                      <p className="text-muted-foreground font-medium">
                        {exp.role}
                      </p>
                      <p className="text-sm text-muted-foreground/80">
                        {exp.period} | {exp.location}
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-2 ml-4">
                    {exp.highlights.map((highlight, idx) => (
                      <li key={idx} className="text-sm text-muted-foreground flex gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
          </div>
        </div>

        {/* Education & Certifications Grid */}
        <div className="grid md:grid-cols-2 gap-12 mt-12">

          {/* Education */}
          <div>
            <h3 className="text-2xl font-semibold mb-6 text-secondary">
              Education
            </h3>
            <div className="space-y-6">
              {education.map((edu) => (
                <Card 
                  key={edu.institution}
                  className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow hover:scale-105 transition-transform"
                >
                  <div className="flex items-center gap-4">
                    <img 
                      src={edu.logo} 
                      alt={edu.institution}
                      className="h-16 w-16 object-contain bg-white p-2 rounded"
                    />
                    <div>
                      <h4 className="text-xl font-semibold text-foreground">
                        {edu.institution}
                      </h4>
                      <p className="text-muted-foreground font-medium">
                        {edu.degree}
                      </p>
                      {edu.details && (
                        <p className="text-sm text-primary">
                          {edu.details}
                        </p>
                      )}
                      <p className="text-sm text-muted-foreground/80">
                        {edu.period} | {edu.location}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
          {/* Certifications */}
          <div>
            <h3 className="text-2xl font-semibold mb-6 text-secondary">
              Certifications
            </h3>
            <div className="space-y-6">
              {certifications.map((cert) => (
                <Card 
                  key={cert.name}
                  className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow hover:scale-105 transition-transform"
                >
                  <div className="flex items-center gap-4">
                    <img 
                      src={cert.logo} 
                      alt={cert.name}
                      className="h-16 w-16 object-contain bg-white p-2 rounded"
                    />
                    <div>
                      <h4 className="text-xl font-semibold text-foreground">
                        {cert.name}
                      </h4>
                      <p className="text-muted-foreground">
                        {cert.issuer}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
