import { Button } from "@/components/ui/button";
import { Github, Linkedin, ExternalLink } from "lucide-react";
import galaxyHero from "@/assets/galaxy-hero.jpg";

export const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url(${galaxyHero})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      >
        <div className="absolute inset-0 bg-background/70" />
      </div>

      {/* Floating Stars */}
      <div className="absolute inset-0 z-0">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute bg-foreground rounded-full animate-pulse"
            style={{
              width: Math.random() * 3 + 1 + 'px',
              height: Math.random() * 3 + 1 + 'px',
              top: Math.random() * 100 + '%',
              left: Math.random() * 100 + '%',
              animationDelay: Math.random() * 3 + 's',
              animationDuration: Math.random() * 2 + 2 + 's',
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="container relative z-10 mx-auto px-4 text-center animate-fade-in">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 glow-text">
          Utkarsh Pathak
        </h1>
        <p className="text-xl md:text-2xl mb-4 text-muted-foreground">
          Data Analyst | AI Enthusiast | Business Intelligence
        </p>
        <p className="text-lg md:text-xl mb-8 max-w-2xl mx-auto text-muted-foreground">
          Transforming data into actionable insights with advanced analytics and machine learning
        </p>
        
        <div className="flex gap-4 justify-center mb-8">
          <Button asChild size="lg" className="bg-primary hover:bg-primary/80">
            <a href="#projects">View Projects</a>
          </Button>
          <Button asChild size="lg" variant="outline" className="border-primary text-primary hover:bg-primary/10">
            <a href="#contact">Contact Me</a>
          </Button>
        </div>

        <div className="flex gap-6 justify-center">
          <a 
            href="https://www.linkedin.com/in/utkarshpathakmsba/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-foreground hover:text-primary transition-colors"
          >
            <Linkedin size={28} />
          </a>
          <a 
            href="https://github.com/utkarsh-portfolio/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-foreground hover:text-primary transition-colors"
          >
            <Github size={28} />
          </a>
          <a 
            href="https://public.tableau.com/app/profile/utkarsh.pathak4808/vizzes" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-foreground hover:text-primary transition-colors"
          >
            <ExternalLink size={28} />
          </a>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce z-10">
        <div className="w-6 h-10 border-2 border-primary rounded-full flex justify-center">
          <div className="w-1 h-3 bg-primary rounded-full mt-2 animate-pulse" />
        </div>
      </div>
    </section>
  );
};
