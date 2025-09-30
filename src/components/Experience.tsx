import { Card } from "@/components/ui/card";
import deloitteLogo from "@/assets/deloitte-logo.jpg";
import featuredLogo from "@/assets/featured.jpg";
import uaLogo from "@/assets/university-arizona.jpg";
import nagpurLogo from "@/assets/nagpur-university.png";

export const Experience = () => {
  const experiences = [
    {
      company: "Deloitte",
      logo: deloitteLogo,
      role: "Data Analyst",
      type: "experience"
    },
    {
      company: "Featured",
      logo: featuredLogo,
      role: "Analytics Consultant",
      type: "experience"
    }
  ];

  const education = [
    {
      institution: "University of Arizona",
      logo: uaLogo,
      degree: "Master's Degree",
      type: "education"
    },
    {
      institution: "Nagpur University",
      logo: nagpurLogo,
      degree: "Bachelor's Degree",
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
                      <p className="text-muted-foreground">
                        {exp.role}
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
                      <p className="text-muted-foreground">
                        {edu.degree}
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
