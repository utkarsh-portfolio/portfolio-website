import { Card } from "@/components/ui/card";
import alteryxLogo from "@/assets/alteryx-logo.jpg";
import databricksLogo from "@/assets/databricks.png";

export const Skills = () => {
  const technologies = [
    { name: "Alteryx", logo: alteryxLogo },
    { name: "Databricks", logo: databricksLogo },
  ];

  const skillCategories = [
    {
      title: "Data Analytics",
      skills: ["Python", "R", "SQL", "Tableau", "Power BI", "Excel"]
    },
    {
      title: "Machine Learning",
      skills: ["Scikit-learn", "TensorFlow", "PyTorch", "NLP", "Computer Vision"]
    },
    {
      title: "Cloud & Tools",
      skills: ["AWS", "Azure", "Git", "Docker", "Jupyter", "VS Code"]
    },
    {
      title: "Business Intelligence",
      skills: ["Data Modeling", "ETL", "Data Warehousing", "Dashboard Design"]
    }
  ];

  return (
    <section id="skills" className="py-20 px-4 bg-muted/20">
      <div className="container mx-auto max-w-6xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          Skills & Technologies
        </h2>

        {/* Featured Technologies */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {technologies.map((tech) => (
            <Card 
              key={tech.name}
              className="bg-card/50 backdrop-blur-sm border-border p-8 card-glow hover:scale-105 transition-transform"
            >
              <img 
                src={tech.logo} 
                alt={tech.name}
                className="h-16 object-contain mx-auto"
              />
            </Card>
          ))}
        </div>

        {/* Skill Categories */}
        <div className="grid md:grid-cols-2 gap-6">
          {skillCategories.map((category) => (
            <Card 
              key={category.title}
              className="bg-card/50 backdrop-blur-sm border-border p-6 card-glow"
            >
              <h3 className="text-xl font-semibold mb-4 text-primary">
                {category.title}
              </h3>
              <div className="flex flex-wrap gap-2">
                {category.skills.map((skill) => (
                  <span 
                    key={skill}
                    className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm border border-primary/30"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
