import "./Navbar.css";
import NavbarButtonsList from "./NavbarButtonsList/NavbarButtonsList";
import minLogoImg from "../../assets/img/logo-min.svg";

const Navbar = () => {
    const mainBtnsData = [
        {
            icon: "icon-home",
        },
        {
            icon: "icon-videochat"
        }
    ];
    const bottomBtnsData = [
        {
            icon: "icon-bell"
        },
        {
            icon: "icon-moon"
        }
    ];

    return (
        <nav className="nav ph-100">
            <div className="nav__content">
                <div className="nav__header">
                    <a href="#" className="nav-logo-link">
                        <img
                            src={ minLogoImg }
                            alt="Min Logo"
                            className="nav-logo"
                        />
                    </a>
                    <hr className="nav__line" />
                    <NavbarButtonsList className="nav-main" btnPostfixClassName="nav-btn" data={ mainBtnsData } />
                </div>
                <NavbarButtonsList className="nav-footer" btnPostfixClassName="nav-btn" data={ bottomBtnsData } />
            </div>
        </nav>
    );
};

export default Navbar;
