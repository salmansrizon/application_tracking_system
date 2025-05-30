const Footer = () => {
  return (
    <footer className="bg-gray-700 text-white p-4 text-center">
      <div className="container mx-auto">
        <p>&copy; {new Date().getFullYear()} Application Tracker. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;
