import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Github, ExternalLink } from "lucide-react";

export const Projects = () => {
  const projects = [
    {
      title: "Healthy-U Calories",
      description: "Agentic AI application that calculates calories in food and suggests healthy alternatives for ingredients. Built with advanced AI models to provide personalized nutrition recommendations.",
      technologies: ["Python", "AI/ML", "NLP", "Web App"],
      github: "https://github.com/utkarsh-portfolio/healthy-u-calories",
      link: null
    },
    {
      title: "AI Agent for Research & Writing",
      description: "Agentic AI system that streamlines research by identifying cutting-edge trends, analyzing pros and cons, and crafting compelling, easy-to-understand articles about tech advancements.",
      technologies: ["Python", "AI Agents", "NLP", "Content Generation"],
      github: "https://github.com/utkarsh-portfolio/AI-Agent-for-Research-And-Writing",
      link: null
    },
    {
      title: "Doctor Visits Prediction",
      description: "Machine learning project analyzing healthcare utilization patterns for patients over 65 years old. Employs various ML techniques to predict and explore patterns in medical consultations.",
      technologies: ["R", "Machine Learning", "Healthcare Analytics", "Statistical Modeling"],
      github: "https://github.com/utkarsh-portfolio/National-Public-Health-Authority",
      link: null
    },
    {
      title: "Credit Card Customer Analytics",
      description: "Comprehensive prescriptive and descriptive analytics project for a credit card company. Features interactive Tableau dashboards for exploratory data analysis and business insights.",
      technologies: ["Tableau", "Data Analytics", "Business Intelligence", "Dashboard Design"],
      github: null,
      link: "https://public.tableau.com/app/profile/utkarsh.pathak4808/viz/creditcard_17331126738590/ExploratoryDashboard"
    }
  ];

  return (
    <section id="projects" className="py-20 px-4">
      <div className="container mx-auto max-w-6xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          Featured Projects
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {projects.map((project) => (
            <Card 
              key={project.title}
              className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow hover:scale-105 transition-transform group"
            >
              <h3 className="text-2xl font-bold mb-3 text-primary group-hover:glow-text transition-all">
                {project.title}
              </h3>
              <p className="text-muted-foreground mb-4">
                {project.description}
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                {project.technologies.map((tech) => (
                  <span 
                    key={tech}
                    className="px-2 py-1 bg-secondary/20 text-secondary text-xs rounded border border-secondary/30"
                  >
                    {tech}
                  </span>
                ))}
              </div>
              <div className="flex gap-3">
                {project.github && (
                  <Button asChild variant="outline" size="sm" className="border-primary text-primary hover:bg-primary/10">
                    <a href={project.github} target="_blank" rel="noopener noreferrer">
                      <Github className="mr-2 h-4 w-4" />
                      Code
                    </a>
                  </Button>
                )}
                {project.link && (
                  <Button asChild variant="outline" size="sm" className="border-secondary text-secondary hover:bg-secondary/10">
                    <a href={project.link} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" />
                      View
                    </a>
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
