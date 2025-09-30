import { Card } from "@/components/ui/card";

export const About = () => {
  return (
    <section id="about" className="py-20 px-4">
      <div className="container mx-auto max-w-4xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          About Me
        </h2>
        
        <Card className="bg-card/50 backdrop-blur-sm border-border p-8 card-glow">
          <div className="space-y-6 text-lg text-muted-foreground">
            <p>
              I'm a passionate Data Analyst with a strong foundation in business intelligence, 
              machine learning, and AI-driven solutions. My expertise spans across various 
              analytical tools and programming languages, enabling me to extract meaningful 
              insights from complex datasets.
            </p>
            <p>
              With experience at leading organizations like Deloitte, I've developed end-to-end 
              data solutions that drive business decisions. My work combines technical prowess 
              with strategic thinking to deliver impactful results.
            </p>
            <p>
              I'm particularly interested in leveraging AI and machine learning to solve 
              real-world problems, from health analytics to automated research systems. 
              My goal is to make data accessible and actionable for everyone.
            </p>
          </div>
        </Card>
      </div>
    </section>
  );
};
