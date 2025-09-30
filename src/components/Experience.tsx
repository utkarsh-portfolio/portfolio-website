import { Card } from "@/components/ui/card";
import deloitteLogo from "@/assets/deloitte-logo.jpg";
import featuredLogo from "@/assets/featured.jpg";
import uaLogo from "@/assets/university-arizona.jpg";
import nagpurLogo from "@/assets/nagpur-university.png";

export const Experience = () => {
  const experiences = [
    {
      company: "Featured (Terkel Inc.)",
      logo: featuredLogo,
      role: "Software Engineer Intern – Data Science",
      period: "July 2025 – September 2025",
      location: "Scottsdale, Arizona",
      type: "experience"
    },
    {
      company: "University of Arizona",
      logo: uaLogo,
      role: "Student Worker, Planning & Operations",
      period: "October 2024 – May 2025",
      location: "Phoenix, Arizona",
      type: "experience"
    },
    {
      company: "Deloitte Consulting",
      logo: deloitteLogo,
      role: "Analyst, AI & Data Engineering Practice",
      period: "January 2021 – August 2024",
      location: "Hyderabad, India",
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

  return (
    <section id="experience" className="py-20 px-4 bg-muted/20">
      <div className="container mx-auto max-w-6xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          Experience & Education
        </h2>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Experience */}
          <div>
            <h3 className="text-2xl font-semibold mb-6 text-primary">
              Professional Experience
            </h3>
            <div className="space-y-6">
              {experiences.map((exp) => (
                <Card 
                  key={exp.company}
                  className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow hover:scale-105 transition-transform"
                >
                  <div className="flex items-center gap-4">
                    <img 
                      src={exp.logo} 
                      alt={exp.company}
                      className="h-16 w-16 object-contain bg-white p-2 rounded"
                    />
                    <div>
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
                </Card>
              ))}
            </div>
          </div>

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
        </div>
      </div>
    </section>
  );
};
