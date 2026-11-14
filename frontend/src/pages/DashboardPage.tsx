import './DashboardPage.css';
import './panel.css';
import './mobile-nav.css';
import Sidebar from '../components/Sidebar/Sidebar';
// import RoomOptions from '../components/RoomOptions/RoomOptions';
import Navbar from '../components/Navbar/Navbar';
// import NoAccess from '../components/NoAccess/NoAccess';
import Room from '../components/Room/Room';
// import PageError from '../components/PageError/NotFound';

const DashboardPage = () => {
    return (
        <section className="dashboard">
            <Navbar />
            <Sidebar />
            {/* <RoomOptions /> */}
            {/* <PageError code={ 500 } /> */}
            {/* <NoAccess isOwner={true} /> */}
            <Room />
        </section>
    );
};

export default DashboardPage;
