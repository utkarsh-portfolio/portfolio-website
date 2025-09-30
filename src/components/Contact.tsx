import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Github, Linkedin, ExternalLink, Mail } from "lucide-react";

export const Contact = () => {
  const socialLinks = [
    {
      name: "LinkedIn",
      url: "https://www.linkedin.com/in/utkarshpathakmsba/",
      icon: Linkedin,
      color: "text-[#0077b5]"
    },
    {
      name: "GitHub",
      url: "https://github.com/utkarsh-portfolio/",
      icon: Github,
      color: "text-foreground"
    },
    {
      name: "Tableau Public",
      url: "https://public.tableau.com/app/profile/utkarsh.pathak4808/vizzes",
      icon: ExternalLink,
      color: "text-[#E97627]"
    }
  ];

  return (
    <section id="contact" className="py-20 px-4">
      <div className="container mx-auto max-w-4xl">
        <h2 className="text-4xl md:text-5xl font-bold mb-12 text-center glow-text">
          Let's Connect
        </h2>

        <Card className="bg-card/50 backdrop-blur-sm border-border p-8 md:p-12 card-glow text-center">
          <Mail className="w-16 h-16 mx-auto mb-6 text-primary" />
          <h3 className="text-2xl font-semibold mb-4">
            Get In Touch
          </h3>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            I'm always interested in hearing about new opportunities, collaborations, 
            or just connecting with fellow data enthusiasts. Feel free to reach out!
          </p>
          
          <div className="mb-8 space-y-2">
            <p className="text-lg text-foreground">
              📧 <a href="mailto:workwithutkarsh22@gmail.com" className="text-primary hover:underline">workwithutkarsh22@gmail.com</a>
            </p>
            <p className="text-lg text-foreground">
              📞 <a href="tel:+16022180453" className="text-primary hover:underline">(602) 218-0453</a>
            </p>
            <p className="text-lg text-foreground">
              📍 Tempe, Arizona
            </p>
          </div>

          <div className="flex flex-wrap gap-4 justify-center mb-8">
            {socialLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Button 
                  key={link.name}
                  asChild 
                  variant="outline" 
                  size="lg"
                  className="border-primary hover:bg-primary/10"
                >
                  <a 
                    href={link.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-2"
                  >
                    <Icon className={`h-5 w-5 ${link.color}`} />
                    {link.name}
                  </a>
                </Button>
              );
            })}
          </div>

          <p className="text-sm text-muted-foreground">
            Available for freelance projects and full-time opportunities
          </p>
        </Card>
      </div>
    </section>
  );
};
