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
              I'm a Data Analyst and AI & Data Engineering professional with a Master's in Business Analytics 
              from the University of Arizona's Eller College of Management (GPA: 3.85/4.00, Dean's List). 
              My expertise spans business intelligence, machine learning, and cloud-based data solutions.
            </p>
            <p>
              With nearly 4 years at Deloitte Consulting, I've guided Fortune 100 executives in architecting 
              data modernization strategies and built real-time pipelines integrating Oracle, SAP, and payment APIs. 
              I've led complex data cloud migrations using AWS services, reducing report latency by 40% while 
              maintaining 99.9% uptime.
            </p>
            <p>
              Currently pursuing opportunities in data engineering and analytics, I'm passionate about leveraging 
              AI/ML, cloud platforms (Databricks, Snowflake, AWS, Azure), and advanced analytics to transform 
              complex data into actionable insights that drive strategic business decisions.
            </p>
          </div>
        </Card>
      </div>
    </section>
  );
};
