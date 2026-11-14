const MobileNav = () => {
    return (
        <nav className="mobile-nav ">
            <div className="mobile-nav__header">
                <a href="#" className="nav-logo-link">
                    <img
                        src="./img/logo-min.svg"
                        alt="Min Logo"
                        className="nav-logo"
                    />
                </a>
                <button className="btn-icon icon icon-menu gray-bg mobile-nav__burger-btn"></button>
            </div>
            <div className="mobile-nav__content ">
                <ul className="mobile-nav-btn-list">
                    <li className="mobile-nav-btn-list-item"><button className="mobile-nav-btn">Dashboard</button></li>
                    <li className="mobile-nav-btn-list-item"><button className="mobile-nav-btn">My Room</button></li>
                </ul>
                <div className="mobile-nav__bottom"></div>
            </div>
        </nav>
    );
};

export default MobileNav;
